import { GoogleGenerativeAI } from '@google/generative-ai';
import { env } from './env';

/**
 * Gemini API Client Configuration
 * Initializes the Google Generative AI client with API key
 */
export const geminiClient = new GoogleGenerativeAI(env.GEMINI_API_KEY);

/**
 * Model Configuration
 * Using Gemini 2.5 Flash for optimal function calling performance
 */
// List of preferred models in order
const MODEL_PRIORITY = ['gemini-2.5-flash', 'gemini-2.5-flash-lite'];

// Track which model is currently in use
let currentModelIndex = 0;

export function getCurrentModelName() {
    return MODEL_PRIORITY[currentModelIndex];
}

// Call this when a quota error is detected to switch to the next model
export function switchToNextModel() {
    if (currentModelIndex < MODEL_PRIORITY.length - 1) {
        currentModelIndex++;
        return true;
    }
    return false; // No more models to try
}

/**
 * Generation Configuration
 * - temperature: 1.0 (default for Gemini 3 models as per best practices)
 * - maxOutputTokens: Reasonable limit for pharmacy responses
 */
export const GENERATION_CONFIG = {
    temperature: 1.0, // Keep at 1.0 for Gemini 3 models to avoid unexpected behavior
    maxOutputTokens: 2048,
    topP: 0.95,
};

/**
 * Safety Settings
 * Configure content safety thresholds for medical content
 */
export const SAFETY_SETTINGS = [
    {
        category: 'HARM_CATEGORY_HARASSMENT' as const,
        threshold: 'BLOCK_MEDIUM_AND_ABOVE' as const,
    },
    {
        category: 'HARM_CATEGORY_HATE_SPEECH' as const,
        threshold: 'BLOCK_MEDIUM_AND_ABOVE' as const,
    },
    {
        category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT' as const,
        threshold: 'BLOCK_MEDIUM_AND_ABOVE' as const,
    },
    {
        category: 'HARM_CATEGORY_DANGEROUS_CONTENT' as const,
        threshold: 'BLOCK_MEDIUM_AND_ABOVE' as const,
    },
];

/**
 * Get configured Gemini model instance
 * Ready for function calling with proper safety settings
 */
export const getGeminiModel = () => {
    return geminiClient.getGenerativeModel({
        model: getCurrentModelName(),
        generationConfig: GENERATION_CONFIG,
        safetySettings: SAFETY_SETTINGS,
    });
};
