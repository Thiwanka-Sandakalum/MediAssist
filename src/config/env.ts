import dotenv from 'dotenv';
import { z } from 'zod';

// Load environment variables from .env file
dotenv.config();

/**
 * Environment variables schema validation using Zod
 * Ensures all required configuration is present and valid
 */
const envSchema = z.object({
    // Gemini API Configuration
    GEMINI_API_KEY: z.string().min(1, 'GEMINI_API_KEY is required'),

    // Server Configuration
    PORT: z.string().default('3000').transform(Number),
    NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),

    // OpenFDA API Configuration (optional - FDA API doesn't require key for basic use)
    OPENFDA_API_KEY: z.string().optional(),
});

/**
 * Parse and validate environment variables
 * Throws error if validation fails
 */
const parseEnv = () => {
    try {
        return envSchema.parse(process.env);
    } catch (error) {
        if (error instanceof z.ZodError) {
            const missingVars = error.errors.map((err) => `${err.path.join('.')}: ${err.message}`);
            throw new Error(`Environment validation failed:\n${missingVars.join('\n')}`);
        }
        throw error;
    }
};

/**
 * Validated environment configuration
 * Use this throughout the application for type-safe env access
 */
export const env = parseEnv();

/**
 * Type-safe environment variables
 */
export type Environment = z.infer<typeof envSchema>;
