/**
 * Agent Types
 * Type definitions for the agent system
 */

import { FunctionDeclarationSchemaType } from '@google/generative-ai';

/**
 * User message sent to the agent
 */
export interface AgentRequest {
    message: string;
}

/**
 * Agent response to user
 */
export interface AgentResponse {
    answer: string;
}

/**
 * Agent execution step for logging and debugging
 */
export enum AgentStep {
    REASON = 'REASON',      // Gemini analyzes user intent
    ACT = 'ACT',           // Tool is executed
    OBSERVE = 'OBSERVE',   // Tool result is received
    SYNTHESIZE = 'SYNTHESIZE', // Final response is generated
}

/**
 * Safety check result
 */
export interface SafetyCheckResult {
    isSafe: boolean;
    refusalReason?: string;
}

/**
 * Function call from Gemini
 */
export interface FunctionCallData {
    name: string;
    args: Record<string, any>;
}
