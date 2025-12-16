import { z } from 'zod';
import sqlite3 from 'sqlite3';
import path from 'path';

// JSON Schema for Gemini function parameters
export const placeOrderParams = {
    type: 'object',
    properties: {
        drug_name: {
            type: 'string',
            description: 'Brand or generic name of the drug to order',
        },
        quantity: {
            type: 'integer',
            description: 'Number of units to order',
            minimum: 1,
        },
        user_name: {
            type: 'string',
            description: 'Name of the person placing the order',
        },
        address: {
            type: 'string',
            description: 'Delivery address for the order',
        },
        phone: {
            type: 'string',
            description: 'Contact phone number',
        },
        payment_method: {
            type: 'string',
            description: 'Payment method (cash, card, mobile)',
            enum: ['cash', 'card', 'mobile'],
        },
    },
    required: ['drug_name', 'quantity', 'user_name', 'address', 'phone', 'payment_method'],
};

// Zod schema for validation
const placeOrderSchema = z.object({
    drug_name: z.string().min(1),
    quantity: z.number().int().min(1),
    user_name: z.string().min(1),
    address: z.string().min(1),
    phone: z.string().min(6),
    payment_method: z.enum(['cash', 'card', 'mobile']),
});

export type PlaceOrderParams = z.infer<typeof placeOrderSchema>;

export const placeOrderFunctionDeclaration = {
    name: 'place_order',
    description:
        'Place a new pharmacy order. If any required info is missing, ask the user for it. Handles all order details and returns confirmation.',
    parameters: placeOrderParams,
};

const DB_PATH = path.resolve(process.cwd(), 'pharmacy_sim.db');

export async function placeOrder(params: PlaceOrderParams): Promise<string> {
    const { drug_name, quantity, user_name, address, phone, payment_method } = params;
    const db = new sqlite3.Database(DB_PATH);

    // Find user or create if not exists
    let userId: number | null = null;
    const userRow = await new Promise<any>((resolve) => {
        db.get(
            'SELECT id FROM users WHERE full_name = ? AND phone = ?',
            [user_name, phone],
            (err, row) => resolve(row)
        );
    });
    if (userRow && userRow.id) {
        userId = userRow.id;
    } else {
        const result = await new Promise<any>((resolve) => {
            db.run(
                'INSERT INTO users (username, password_hash, full_name, email, phone, address, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                [
                    user_name.toLowerCase().replace(/\s+/g, '') + Math.floor(Math.random() * 10000),
                    Math.random().toString(36).slice(2),
                    user_name,
                    user_name.toLowerCase().replace(/\s+/g, '') + '@example.com',
                    phone,
                    address,
                    'customer',
                    new Date().toISOString().slice(0, 10),
                ],
                function (this: any, err) {
                    resolve({ id: this.lastID });
                }
            );
        });
        userId = result.id;
    }

    // Find inventory item
    const inventoryRow = await new Promise<any>((resolve) => {
        db.get(
            `SELECT i.id, i.price_lkr, i.stock_count, d.brand_name, d.generic_name
       FROM inventory i
       JOIN drugs d ON i.drug_id = d.id
       WHERE (LOWER(d.brand_name) LIKE ? OR LOWER(d.generic_name) LIKE ?) AND i.stock_count >= ?
       ORDER BY i.stock_count DESC
       LIMIT 1`,
            [`%${drug_name.toLowerCase()}%`, `%${drug_name.toLowerCase()}%`, quantity],
            (err, row) => resolve(row)
        );
    });
    if (!inventoryRow) {
        db.close();
        return `Sorry, we do not have enough stock of "${drug_name}" to fulfill your order.`;
    }

    // Create order
    const orderResult = await new Promise<any>((resolve) => {
        db.run(
            'INSERT INTO orders (user_id, order_date, status, total_price_lkr, shipping_address, payment_method, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [
                userId,
                new Date().toISOString().slice(0, 10),
                'pending',
                inventoryRow.price_lkr * quantity,
                address,
                payment_method,
                '',
            ],
            function (this: any, err) {
                resolve({ id: this.lastID });
            }
        );
    });
    const orderId = orderResult.id;

    // Create order item
    await new Promise<void>((resolve) => {
        db.run(
            'INSERT INTO order_items (order_id, inventory_id, quantity, unit_price_lkr, subtotal_lkr) VALUES (?, ?, ?, ?, ?)',
            [orderId, inventoryRow.id, quantity, inventoryRow.price_lkr, inventoryRow.price_lkr * quantity],
            () => resolve()
        );
    });

    // Update inventory
    await new Promise<void>((resolve) => {
        db.run(
            'UPDATE inventory SET stock_count = stock_count - ? WHERE id = ?',
            [quantity, inventoryRow.id],
            () => resolve()
        );
    });

    db.close();
    return `Order placed! ${inventoryRow.brand_name || inventoryRow.generic_name}, Qty: ${quantity}, Total: LKR ${inventoryRow.price_lkr * quantity}, Order ID: ${orderId}`;
}
