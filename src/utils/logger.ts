import { env } from '../config/env';

/**
 * Logger Utility
 * Simple structured logging for production debugging
 */

enum LogLevel {
    INFO = 'INFO',
    WARN = 'WARN',
    ERROR = 'ERROR',
    DEBUG = 'DEBUG',
}

class Logger {
    private isDevelopment: boolean;

    constructor() {
        this.isDevelopment = env.NODE_ENV === 'development';
    }

    /**
     * Format log message with timestamp and level
     */
    private format(level: LogLevel, message: string, meta?: any): string {
        const timestamp = new Date().toISOString();
        const metaStr = meta ? `\n${JSON.stringify(meta, null, 2)}` : '';
        return `[${timestamp}] [${level}] ${message}${metaStr}`;
    }

    /**
     * Log info message
     */
    info(message: string, meta?: any): void {
        console.log(this.format(LogLevel.INFO, message, meta));
    }

    /**
     * Log warning message
     */
    warn(message: string, meta?: any): void {
        console.warn(this.format(LogLevel.WARN, message, meta));
    }

    /**
     * Log error message
     */
    error(message: string, error?: any): void {
        const errorMeta = error instanceof Error
            ? { message: error.message, stack: error.stack }
            : error;
        console.error(this.format(LogLevel.ERROR, message, errorMeta));
    }

    /**
     * Log debug message (only in development)
     */
    debug(message: string, meta?: any): void {
        if (this.isDevelopment) {
            console.debug(this.format(LogLevel.DEBUG, message, meta));
        }
    }

    /**
     * Log agent step (useful for debugging agent loops)
     */
    agentStep(step: string, details?: any): void {
        this.info(`🤖 Agent Step: ${step}`, details);
    }

    /**
     * Log tool execution
     */
    toolExecution(toolName: string, params: any): void {
        this.info(`🔧 Tool Execution: ${toolName}`, params);
    }

    /**
     * Log API request
     */
    apiRequest(method: string, url: string, params?: any): void {
        this.debug(`📡 API Request: ${method} ${url}`, params);
    }

    /**
     * Log API response
     */
    apiResponse(url: string, status: number, data?: any): void {
        this.debug(`📥 API Response: ${url} [${status}]`, data);
    }
}

/**
 * Singleton logger instance
 */
export const logger = new Logger();
