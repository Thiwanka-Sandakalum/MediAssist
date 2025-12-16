import express, { Application, Request, Response, NextFunction } from 'express';
import { agentRouter } from './api/agent.controller';
import { logger } from './utils/logger';

/**
 * Express Application Setup
 * Configures middleware and routes
 */

/**
 * Create and configure Express app
 */
export function createApp(): Application {
    const app = express();

    // ===========================
    // MIDDLEWARE
    // ===========================

    // Parse JSON request bodies
    app.use(express.json());

    // Parse URL-encoded bodies
    app.use(express.urlencoded({ extended: true }));

    // Request logging middleware
    app.use((req: Request, res: Response, next: NextFunction) => {
        logger.info(`${req.method} ${req.path}`, {
            ip: req.ip,
            userAgent: req.get('user-agent'),
        });
        next();
    });

    // CORS headers (adjust for production)
    app.use((req: Request, res: Response, next: NextFunction) => {
        res.header('Access-Control-Allow-Origin', '*');
        res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');

        if (req.method === 'OPTIONS') {
            res.sendStatus(200);
            return;
        }

        next();
    });

    // ===========================
    // ROUTES
    // ===========================

    // Root endpoint
    app.get('/', (req: Request, res: Response) => {
        res.json({
            service: 'MediAssist Backend',
            version: '1.0.0',
            description: 'Agentic pharmacy assistant powered by Gemini and openFDA',
            endpoints: {
                chat: 'POST /agent/chat',
                health: 'GET /agent/health',
            },
        });
    });

    // Agent routes
    app.use('/agent', agentRouter);

    // ===========================
    // ERROR HANDLING
    // ===========================

    // 404 handler
    app.use((req: Request, res: Response) => {
        logger.warn(`404 Not Found: ${req.method} ${req.path}`);
        res.status(404).json({
            error: 'Not Found',
            message: `Route ${req.method} ${req.path} does not exist`,
        });
    });

    // Global error handler
    app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
        logger.error('Unhandled error', err);

        res.status(500).json({
            error: 'Internal Server Error',
            message: 'An unexpected error occurred',
        });
    });

    return app;
}
