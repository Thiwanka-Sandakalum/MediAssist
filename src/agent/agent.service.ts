import { Content, Part, FunctionCall, GenerateContentResult } from '@google/generative-ai';
import { getGeminiModel, switchToNextModel } from '../config/gemini';
import { logger } from '../utils/logger';
import { ChatLogger } from '../utils/chatLogger';
import { openFDAFunctionDeclaration, queryOpenFDA, QueryOpenFDAParams } from '../tools/openfda.tool';
import { inventoryAvailabilityFunctionDeclaration, checkInventoryAvailability, InventoryAvailabilityParams } from '../tools/inventory.tool';
import { placeOrderFunctionDeclaration, placeOrder, PlaceOrderParams } from '../tools/order.tool';
import { getOrderStatusFunctionDeclaration, getOrderStatus } from '../tools/orderStatus.tool';
import { SYSTEM_PROMPT, SAFETY_KEYWORDS, REFUSAL_TEMPLATES } from './agent.prompt';
import { listOrdersByPhoneFunctionDeclaration, listOrdersByPhone } from '../tools/listOrders.tool';
import { AgentRequest, AgentResponse, AgentStep, SafetyCheckResult } from './agent.types';
import fs from 'fs';
import path from 'path';
import { OrderSessionManager, REQUIRED_ORDER_FIELDS } from './orderSessionManager';

const orderSessionManager = new OrderSessionManager();

/**
 * Agent Service
 * Orchestrates the Reason → Act → Observe → Synthesize loop
 * 
 * ARCHITECTURE:
 * 1. Receive user message
 * 2. Check safety (refuse dangerous queries)
 * 3. Send to Gemini with function declarations
 * 4. If Gemini calls a function:
 *    - Execute the function
 *    - Send result back to Gemini
 *    - Repeat until Gemini provides final answer
 * 5. Return final answer with safety disclaimer
 */
export class AgentService {
    private model;
    private tools;
    private chatSessions: Map<string, any> = new Map(); // userId -> Chat object

    // Load chat history for a user (from file, DB, etc.)
    private loadChatHistory(userId: string): any[] {
        const file = this.getHistoryPath(userId);
        if (fs.existsSync(file)) {
            try {
                return JSON.parse(fs.readFileSync(file, 'utf-8'));
            } catch {
                return [];
            }
        }
        return [];
    }

    // Save chat history for a user
    private async saveChatHistory(userId: string, chat: any) {
        const history = await chat.getHistory();
        fs.writeFileSync(this.getHistoryPath(userId), JSON.stringify(history, null, 2));
    }

    // Helper functions for chat history persistence (simple file-based for demo)
    private getHistoryPath(userId: string) {
        const HISTORY_DIR = path.resolve(process.cwd(), 'chat_history');
        if (!fs.existsSync(HISTORY_DIR)) fs.mkdirSync(HISTORY_DIR);
        return path.join(HISTORY_DIR, `${userId}.json`);
    }

    constructor() {
        // Initialize Gemini model
        this.model = getGeminiModel();

        // Define available tools for Gemini
        this.tools = [
            {
                functionDeclarations: [
                    openFDAFunctionDeclaration,
                    inventoryAvailabilityFunctionDeclaration,
                    placeOrderFunctionDeclaration,
                    getOrderStatusFunctionDeclaration,
                    listOrdersByPhoneFunctionDeclaration,
                ],
            },
        ];
    }

    /**
     * Main agent execution method
     * Implements the full ReAct loop
     */
    async processMessage(request: AgentRequest): Promise<AgentResponse> {
        const userId = request.userId || 'anonymous';
        const startTime = Date.now();
        const functionCallsLog: Array<{ name: string; args: any; result: string }> = [];

        let chat = this.chatSessions.get(userId);
        if (!chat) {
            let history = this.loadChatHistory(userId);
            // Do not limit chat history; use full context window
            chat = this.model.startChat({
                history,
                tools: this.tools,
            });
            this.chatSessions.set(userId, chat);
        }

        // Helper to reset chat with new model
        const resetChatWithNewModel = () => {
            this.model = getGeminiModel();
            let history = this.loadChatHistory(userId);
            // Do not limit chat history; use full context window
            chat = this.model.startChat({
                history,
                tools: this.tools,
            });
            this.chatSessions.set(userId, chat);
        };

        let quotaRetry = false;
        try {
            logger.agentStep(AgentStep.REASON, { userMessage: request.message });

            // STEP 1: Safety check
            const safetyCheck = this.checkSafety(request.message);
            if (!safetyCheck.isSafe) {
                logger.warn('Query refused due to safety rules', { reason: safetyCheck.refusalReason });

                // Log the interaction
                ChatLogger.logInteraction({
                    timestamp: new Date().toISOString(),
                    userId,
                    userMessage: request.message,
                    botResponse: safetyCheck.refusalReason!,
                    functionCalls: [],
                    duration: Date.now() - startTime,
                });

                return {
                    answer: safetyCheck.refusalReason!,
                };
            }

            // STEP 2: Initialize conversation with system prompt
            // const chat = this.model.startChat({
            //     history: [
            //         {
            //             role: 'user',
            //             parts: [{ text: SYSTEM_PROMPT }],
            //         },
            //         {
            //             role: 'model',
            //             parts: [{ text: 'Understood. I will follow all safety rules and use the FDA tool appropriately. I am ready to assist with drug information queries.' }],
            //         },
            //     ],
            //     tools: this.tools,
            // });

            // STEP 3: Send user message to Gemini
            let result;
            try {
                result = await chat.sendMessage(request.message);
            } catch (error: any) {
                // If quota error, try switching model and retry once
                if (
                    error &&
                    typeof error.message === 'string' &&
                    (error.message.includes('quota') || error.message.includes('429 Too Many Requests')) &&
                    switchToNextModel()
                ) {
                    quotaRetry = true;
                    resetChatWithNewModel();
                    result = await chat.sendMessage(request.message);
                } else {
                    throw error;
                }
            }
            let iterationCount = 0;
            const MAX_ITERATIONS = 5; // Prevent infinite loops

            // STEP 4: Agent loop - handle function calls
            while (this.hasFunctionCalls(result) && iterationCount < MAX_ITERATIONS) {
                iterationCount++;
                logger.agentStep(AgentStep.ACT, { iteration: iterationCount });

                // Extract function call
                const functionCall = this.extractFunctionCall(result);
                if (!functionCall) {
                    logger.warn('Function call detected but could not extract details');
                    break;
                }

                logger.toolExecution(functionCall.name, functionCall.args);

                // Execute the function
                const functionResult = await this.executeFunction(functionCall);

                // Truncate function result to minimize token usage in chat history
                const truncatedResult = this.truncateFunctionResult(functionCall.name, functionResult);

                // Log function call
                functionCallsLog.push({
                    name: functionCall.name,
                    args: functionCall.args,
                    result: truncatedResult, // Log truncated version
                });

                logger.agentStep(AgentStep.OBSERVE, {
                    functionName: functionCall.name,
                    resultPreview: truncatedResult.substring(0, 200) + '...',
                });

                // Send truncated function result back to Gemini
                result = await chat.sendMessage([
                    {
                        functionResponse: {
                            name: functionCall.name,
                            response: {
                                result: truncatedResult,
                            },
                        },
                    },
                ]);
            }

            // STEP 5: Extract final text response
            logger.agentStep(AgentStep.SYNTHESIZE);

            const finalAnswer = this.extractTextResponse(result);

            if (!finalAnswer) {
                throw new Error('No valid response generated by the model');
            }

            // Save chat history after each turn
            await this.saveChatHistory(userId, chat);

            // If this turn included a successful order placement, append a feedback prompt
            let answerWithFeedback = finalAnswer;
            if (
                functionCallsLog.some(
                    (call) => call.name === 'place_order' && call.result && call.result.includes('Order placed successfully')
                )
            ) {
                answerWithFeedback += '\n\nWe value your feedback! Was this ordering experience helpful? Reply with any comments or suggestions.';
            }

            ChatLogger.logInteraction({
                timestamp: new Date().toISOString(),
                userId,
                userMessage: request.message,
                botResponse: answerWithFeedback,
                functionCalls: functionCallsLog,
                duration: Date.now() - startTime,
            });

            return {
                answer: answerWithFeedback,
            };

        } catch (error: any) {
            logger.error('Error in agent processing', error);

            let errorMessage = 'I apologize, but I encountered an error while processing your request. Please try rephrasing your question or try again later.';

            // Detect Gemini API quota exceeded (429) and provide a specific message
            if (error && typeof error.message === 'string' && (error.message.includes('429 Too Many Requests') || error.message.includes('quota'))) {
                if (quotaRetry) {
                    errorMessage = 'Sorry, all available models have reached their usage limits. Please try again later or contact support.';
                } else {
                    errorMessage = 'Sorry, we have reached our usage limit for the day. Please try again later or contact support.';
                }
            }

            // Log error interaction
            ChatLogger.logInteraction({
                timestamp: new Date().toISOString(),
                userId,
                userMessage: request.message,
                botResponse: errorMessage,
                functionCalls: functionCallsLog,
                duration: Date.now() - startTime,
            });

            // Graceful error response
            return {
                answer: errorMessage,
            };
        }
    }

    /**
     * Safety check: Detect dangerous queries and refuse them
     */
    private checkSafety(message: string): SafetyCheckResult {
        const lowerMessage = message.toLowerCase();

        // Check for dosing questions
        if (SAFETY_KEYWORDS.dosing.some(keyword => lowerMessage.includes(keyword))) {
            return {
                isSafe: false,
                refusalReason: REFUSAL_TEMPLATES.dosing,
            };
        }

        // Check for children-related queries
        if (SAFETY_KEYWORDS.children.some(keyword => lowerMessage.includes(keyword))) {
            return {
                isSafe: false,
                refusalReason: REFUSAL_TEMPLATES.children,
            };
        }

        // Check for pregnancy/breastfeeding queries
        if (SAFETY_KEYWORDS.pregnancy.some(keyword => lowerMessage.includes(keyword))) {
            return {
                isSafe: false,
                refusalReason: REFUSAL_TEMPLATES.pregnancy,
            };
        }

        // Check for liver/kidney conditions
        if (SAFETY_KEYWORDS.conditions.some(keyword => lowerMessage.includes(keyword))) {
            return {
                isSafe: false,
                refusalReason: REFUSAL_TEMPLATES.conditions,
            };
        }

        // Check for medical advice requests
        if (SAFETY_KEYWORDS.advice.some(keyword => lowerMessage.includes(keyword))) {
            return {
                isSafe: false,
                refusalReason: REFUSAL_TEMPLATES.advice,
            };
        }

        return { isSafe: true };
    }

    /**
     * Check if the result contains function calls
     */
    private hasFunctionCalls(result: GenerateContentResult): boolean {
        const candidate = result.response.candidates?.[0];
        if (!candidate) return false;

        return candidate.content.parts.some(
            (part) => 'functionCall' in part && part.functionCall !== undefined
        );
    }

    /**
     * Extract function call details from the result
     */
    private extractFunctionCall(result: GenerateContentResult): FunctionCall | null {
        const candidate = result.response.candidates?.[0];
        if (!candidate) return null;

        for (const part of candidate.content.parts) {
            if ('functionCall' in part && part.functionCall) {
                return part.functionCall;
            }
        }

        return null;
    }

    /**
     * Execute a function based on the function call
     */
    private async executeFunction(functionCall: FunctionCall): Promise<string> {
        switch (functionCall.name) {
            case 'query_openfda_drug_label':
                return await queryOpenFDA(functionCall.args as QueryOpenFDAParams);
            case 'check_inventory_availability':
                return await checkInventoryAvailability(functionCall.args as InventoryAvailabilityParams);
            case 'place_order':
                return await placeOrder(functionCall.args as PlaceOrderParams);
            case 'get_order_status':
                return await getOrderStatus(functionCall.args as any);
            case 'list_orders_by_phone':
                return await listOrdersByPhone(functionCall.args as { phone: string });
            default:
                logger.warn(`Unknown function call: ${functionCall.name}`);
                return JSON.stringify({
                    success: false,
                    message: `Unknown function: ${functionCall.name}`,
                });
        }
    }

    /**
     * Extract text response from the result
     */
    private extractTextResponse(result: GenerateContentResult): string | null {
        const candidate = result.response.candidates?.[0];
        if (!candidate) return null;

        const textParts = candidate.content.parts
            .filter((part) => 'text' in part && part.text)
            .map((part) => (part as { text: string }).text);

        return textParts.join('\n').trim() || null;
    }

    /**
     * Truncate function results to minimize token usage
     * Different truncation strategies for different function types
     */
    private truncateFunctionResult(_functionName: string, result: string): string {
        // For OpenFDA queries, the result is already pre-truncated by DrugMapper
        // But let's add a safety limit
        const MAX_CHARS = 2000;

        if (result.length <= MAX_CHARS) {
            return result;
        }

        // Truncate and add notice
        const truncated = result.substring(0, MAX_CHARS);

        // Try to preserve the structure if it's JSON
        try {
            const parsedResult = JSON.parse(result);
            if (parsedResult && typeof parsedResult === 'object') {
                return JSON.stringify({
                    ...parsedResult,
                    data: truncated,
                    _truncated: true,
                    _note: 'Result truncated to reduce token usage'
                });
            }
        } catch {
            // If not valid JSON, just return truncated string
        }

        return truncated + '\n\n[Result truncated to reduce token usage]';
    }
}
