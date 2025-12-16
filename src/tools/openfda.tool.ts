import axios, { AxiosError } from 'axios';
import http from 'http';
import https from 'https';
import { z } from 'zod';
import { OpenFDAResponse } from '../domain/drug.entity';
import { DrugMapper } from '../domain/drug.mapper';
import { logger } from '../utils/logger';
import { normalizeDrugName } from '../utils/normalizeDrugName';

/**
 * OpenFDA Tool
 * Provides function for Gemini to query FDA drug label data
 * 
 * ARCHITECTURE:
 * - This is a "tool" that Gemini can call via function calling
 * - It ONLY fetches and structures data - it does NOT format user responses
 * - Gemini decides WHEN to call this and WITH WHAT parameters
 */

/**
 * OpenFDA API Configuration
 */
const OPENFDA_BASE_URL = 'https://api.fda.gov/drug/label.json';
const DEFAULT_LIMIT = 5;
const MAX_LIMIT = 10; // Reasonable limit to avoid overwhelming Gemini

/**
 * Function parameters schema for Gemini
 * Gemini will provide these parameters when calling the function
 */
export const openFDAFunctionParameters = {
    type: 'object' as const,
    properties: {
        search_field: {
            type: 'string' as const,
            description: `The field to search in. Common fields:
        - "openfda.generic_name" - Search by generic drug name (e.g., "acetaminophen")
        - "openfda.brand_name" - Search by brand name (e.g., "Tylenol")
        - "indications_and_usage" - Search in usage/purpose text
        - "adverse_reactions" - Search in side effects
        - "drug_interactions" - Search in interaction warnings
        - "warnings" - Search in warning text
      Use "openfda.generic_name" for general drug queries.`,
            enum: [
                'openfda.generic_name',
                'openfda.brand_name',
                'indications_and_usage',
                'adverse_reactions',
                'drug_interactions',
                'warnings',
            ],
        },
        search_term: {
            type: 'string' as const,
            description: `The term to search for in the specified field. 
        For drug names, use the generic name (e.g., "acetaminophen" not "paracetamol").
        Be specific and use exact terms when possible.`,
        },
        limit: {
            type: 'number' as const,
            description: `Number of results to return (1-10). Default is 5. 
        Use lower values (1-3) for specific drug queries.
        Use higher values (5-10) for broader searches.`,
            default: DEFAULT_LIMIT,
        },
    },
    required: ['search_field', 'search_term'],
};

/**
 * Function declaration for Gemini
 * This tells Gemini what the function does and how to use it
 */
export const openFDAFunctionDeclaration = {
    name: 'query_openfda_drug_label',
    description: `Query the openFDA Drug Label database for authoritative drug information.
    
    Use this function when the user asks about:
    - Drug side effects or adverse reactions
    - Drug warnings or precautions
    - Drug interactions
    - What a drug is used for (indications)
    - General drug information
    
    DO NOT use this function when:
    - The user is just greeting or having casual conversation
    - The question is not about a specific drug
    - The user is asking for personal medical advice (refuse these queries)
    
    ALWAYS normalize drug names before searching (e.g., "paracetamol" → "acetaminophen").`,
    parameters: openFDAFunctionParameters,
};

/**
 * Function call parameters validator
 */
const queryParamsSchema = z.object({
    search_field: z.enum([
        'openfda.generic_name',
        'openfda.brand_name',
        'indications_and_usage',
        'adverse_reactions',
        'drug_interactions',
        'warnings',
    ]),
    search_term: z.string().min(1),
    limit: z.number().min(1).max(MAX_LIMIT).default(DEFAULT_LIMIT),
});

export type QueryOpenFDAParams = z.infer<typeof queryParamsSchema>;

/**
 * Execute openFDA query
 * This is the actual function that gets called when Gemini requests it
 */
export async function queryOpenFDA(params: QueryOpenFDAParams): Promise<string> {
    try {
        // Validate parameters
        const validatedParams = queryParamsSchema.parse(params);

        // Normalize drug name if searching by name
        let searchTerm = validatedParams.search_term;
        if (
            validatedParams.search_field === 'openfda.generic_name' ||
            validatedParams.search_field === 'openfda.brand_name'
        ) {
            searchTerm = normalizeDrugName(validatedParams.search_term);
        }

        // Build query URL with selective field retrieval to minimize token usage
        // Only fetch essential fields instead of ALL fields
        const fieldsToFetch = [
            'openfda.generic_name',
            'openfda.brand_name',
            'purpose',
            'active_ingredient',
            'warnings',
            'adverse_reactions',
            'drug_interactions',
            'contraindications',
            'dosage_and_administration'
        ].join(',');

        const url = `${OPENFDA_BASE_URL}?search=${validatedParams.search_field}:${encodeURIComponent(searchTerm)}&limit=${validatedParams.limit}&fields=${fieldsToFetch}`;

        logger.toolExecution('query_openfda_drug_label', {
            search_field: validatedParams.search_field,
            search_term: searchTerm,
            limit: validatedParams.limit,
            fields: fieldsToFetch,
        });
        logger.apiRequest('GET', url);

        // Execute API request with IPv4 preference and extended timeout
        const response = await axios.get<OpenFDAResponse>(url, {
            timeout: 30000, // 30 second timeout to handle DNS/connection delays
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'MediAssist-Backend/1.0',
            },
            family: 4, // Force IPv4 to avoid IPv6 issues
            httpAgent: new http.Agent({
                keepAlive: true,
                family: 4
            }),
            httpsAgent: new https.Agent({
                keepAlive: true,
                family: 4,
                rejectUnauthorized: true
            }),
        });

        logger.apiResponse(url, response.status, {
            resultsCount: response.data.results?.length || 0,
        });

        // Handle no results
        if (!response.data.results || response.data.results.length === 0) {
            return JSON.stringify({
                success: false,
                message: `No FDA drug label data found for "${searchTerm}" in field "${validatedParams.search_field}".`,
                suggestion: 'Try searching with a different drug name or check the spelling.',
            });
        }

        // Map FDA results to domain entities
        const drugEntities = DrugMapper.toDrugEntities(response.data.results);

        // Create structured summary for Gemini
        const summaries = drugEntities.map((entity) => DrugMapper.toSummary(entity));

        // Return success with data
        return JSON.stringify({
            success: true,
            resultsCount: drugEntities.length,
            data: summaries,
            disclaimer: 'This information is from FDA drug labels and is for educational purposes only. Always consult a healthcare professional.',
        });

    } catch (error) {
        // Enhanced error logging for Axios
        if (axios.isAxiosError(error)) {
            logger.error('Axios error querying openFDA API', {
                message: error.message,
                code: error.code,
                url: error.config?.url,
                method: error.config?.method,
                response: error.response ? {
                    status: error.response.status,
                    statusText: error.response.statusText,
                    data: error.response.data
                } : undefined
            });
        } else {
            logger.error('Unknown error querying openFDA API', {
                error: error instanceof Error ? error.message : String(error),
                stack: error instanceof Error ? error.stack : undefined
            });
        }

        logger.error('Error querying openFDA', error);

        // Handle specific error cases
        if (axios.isAxiosError(error)) {
            const axiosError = error as AxiosError;

            if (axiosError.response?.status === 404) {
                return JSON.stringify({
                    success: false,
                    message: 'No drug found matching your search criteria.',
                    suggestion: 'Check the drug name spelling or try searching by brand name.',
                });
            }

            if (axiosError.code === 'ECONNABORTED') {
                return JSON.stringify({
                    success: false,
                    message: 'Request to FDA API timed out.',
                    suggestion: 'Please try again.',
                });
            }

            return JSON.stringify({
                success: false,
                message: 'Error communicating with FDA API.',
                error: axiosError.message,
            });
        }

        // Generic error
        return JSON.stringify({
            success: false,
            message: 'An unexpected error occurred while fetching drug information.',
            error: error instanceof Error ? error.message : 'Unknown error',
        });
    }
}
