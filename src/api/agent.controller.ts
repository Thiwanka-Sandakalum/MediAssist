import { Request, Response, Router } from 'express';
import { z } from 'zod';
import { AgentService } from '../agent/agent.service';
import { logger } from '../utils/logger';

/**
 * Agent Controller
 * Handles HTTP requests and delegates to AgentService
 * 
 * ARCHITECTURE:
 * - Controller: Handles HTTP, validation, error responses
 * - Service: Contains business logic and agent orchestration
 * - Clear separation of concerns
 */

/**
 * Request body schema validation
 */
const chatRequestSchema = z.object({
    message: z.string().min(1, 'Message cannot be empty').max(1000, 'Message too long'),
});

/**
 * Agent Controller Class
 */
export class AgentController {
    public router: Router;
    private agentService: AgentService;

    constructor() {
        this.router = Router();
        this.agentService = new AgentService();
        this.initializeRoutes();
    }

    /**
     * Initialize routes
     */
    private initializeRoutes(): void {
        this.router.post('/chat', this.chat.bind(this));
        this.router.get('/health', this.health.bind(this));
    }

    /**
     * POST /agent/chat
     * Main chat endpoint for agent interaction
     */
    private async chat(req: Request, res: Response): Promise<void> {
        try {
            // Validate request body
            const validationResult = chatRequestSchema.safeParse(req.body);

            if (!validationResult.success) {
                logger.warn('Invalid request body', validationResult.error.errors);
                res.status(400).json({
                    error: 'Invalid request',
                    details: validationResult.error.errors.map((err) => ({
                        field: err.path.join('.'),
                        message: err.message,
                    })),
                });
                return;
            }

            const { message } = validationResult.data;

            logger.info('Received chat request', { message });

            // Process message through agent
            const response = await this.agentService.processMessage({ message });

            logger.info('Sending chat response', {
                answerLength: response.answer.length,
            });

            // Send successful response
            res.status(200).json({
                answer: response.answer,
            });

        } catch (error) {
            logger.error('Error in chat endpoint', error);

            // Send error response
            res.status(500).json({
                error: 'Internal server error',
                message: 'An error occurred while processing your request. Please try again.',
            });
        }
    }

    /**
     * GET /agent/health
     * Health check endpoint
     */
    private async health(req: Request, res: Response): Promise<void> {
        res.status(200).json({
            status: 'healthy',
            service: 'MediAssist Agent',
            timestamp: new Date().toISOString(),
        });
    }
}

/**
 * Export router instance
 */
export const agentController = new AgentController();
export const agentRouter = agentController.router;
