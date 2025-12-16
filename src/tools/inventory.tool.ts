import { z } from 'zod';
import sqlite3 from 'sqlite3';
import path from 'path';

/**
 * Provides function for Gemini to check inventory availability
 * - This is a "tool" that Gemini can call via function calling
 */

// Function parameters schema for Gemini
export const inventoryAvailabilityParams = {
    drug_name: {
        type: 'string',
        description: 'Brand or generic name of the drug to check in inventory',
    },
};

// Zod schema for validation
const queryParamsSchema = z.object({
    drug_name: z.string().min(1),
});

export type InventoryAvailabilityParams = z.infer<typeof queryParamsSchema>;

// Function declaration for Gemini
export const inventoryAvailabilityFunctionDeclaration = {
    name: 'check_inventory_availability',
    description:
        'Check if a drug is available in the pharmacy inventory and return price, brand, and stock info. Use this function when the user asks if a medicine is available or wants to order a drug.',
    parameters: {
        type: 'object',
        properties: {
            drug_name: {
                type: 'string',
                description: 'Brand or generic name of the drug to check in inventory',
            },
        },
        required: ['drug_name'],
    },
};

// Path to the SQLite DB (adjust if needed)
const DB_PATH = path.resolve(process.cwd(), 'pharmacy_sim.db');

/**
 * This is the actual function that gets called when Gemini requests it
 */
export async function checkInventoryAvailability(params: InventoryAvailabilityParams): Promise<string> {
    const { drug_name } = params;
    const db = new sqlite3.Database(DB_PATH);

    // Search for the drug by brand or generic name (case-insensitive, partial match)
    const query = `
    SELECT d.brand_name, d.generic_name, i.price_lkr, i.stock_count, d.manufacturer
    FROM drugs d
    JOIN inventory i ON d.id = i.drug_id
    WHERE LOWER(d.brand_name) LIKE ? OR LOWER(d.generic_name) LIKE ?
    ORDER BY i.stock_count DESC
    LIMIT 5;
  `;
    const searchTerm = `%${drug_name.toLowerCase()}%`;

    return new Promise((resolve) => {
        db.all(query, [searchTerm, searchTerm], (err, rows: any[]) => {
            db.close();
            if (err) {
                return resolve('Sorry, there was an error checking inventory.');
            }
            if (!rows || rows.length === 0) {
                return resolve(`Sorry, we do not have "${drug_name}" in stock.`);
            }
            // Format the response
            const lines = rows.map((row) =>
                `Available: ${row.brand_name || row.generic_name} - LKR ${row.price_lkr} (Stock: ${row.stock_count})`
            );
            resolve(lines.join('\n'));
        });
    });
}
