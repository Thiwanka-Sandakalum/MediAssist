import { createApp } from './app';
import { env } from './config/env';
import { logger } from './utils/logger';

/**
 * Server Entry Point
 * Starts the Express server
 */

async function startServer() {
    try {
        // Create Express app
        const app = createApp();

        // Start server
        const server = app.listen(env.PORT, () => {
            logger.info(`🚀 MediAssist Backend started`, {
                port: env.PORT,
                environment: env.NODE_ENV,
                endpoints: {
                    chat: `http://localhost:${env.PORT}/agent/chat`,
                    health: `http://localhost:${env.PORT}/agent/health`,
                },
            });
        });

        // Graceful shutdown
        const gracefulShutdown = (signal: string) => {
            logger.info(`Received ${signal}, shutting down gracefully...`);

            server.close(() => {
                logger.info('Server closed');
                process.exit(0);
            });

            // Force shutdown after 10 seconds
            setTimeout(() => {
                logger.error('Forced shutdown after timeout');
                process.exit(1);
            }, 10000);
        };

        // Listen for termination signals
        process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
        process.on('SIGINT', () => gracefulShutdown('SIGINT'));

        // Handle uncaught errors
        process.on('uncaughtException', (error: Error) => {
            logger.error('Uncaught Exception', error);
            process.exit(1);
        });

        process.on('unhandledRejection', (reason: any) => {
            logger.error('Unhandled Rejection', reason);
            process.exit(1);
        });

    } catch (error) {
        logger.error('Failed to start server', error);
        process.exit(1);
    }
}

// Start the server
startServer();
