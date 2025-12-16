import sqlite3 from 'sqlite3';
import path from 'path';

// JSON Schema for Gemini function parameters
export const getOrderStatusParams = {
    type: 'object',
    properties: {
        order_id: {
            type: 'integer',
            description: 'Order ID to check status for',
            minimum: 1,
        },
        phone: {
            type: 'string',
            description: 'User phone number (for security)',
        },
    },
    required: ['order_id', 'phone'],
};

export const getOrderStatusFunctionDeclaration = {
    name: 'get_order_status',
    description:
        'Get the status and details of a pharmacy order by order ID and phone number. Use this to answer user queries about their order status.',
    parameters: getOrderStatusParams,
};

const DB_PATH = path.resolve(process.cwd(), 'pharmacy_sim.db');

export async function getOrderStatus(params: { order_id: number; phone: string }): Promise<string> {
    const { order_id, phone } = params;
    const db = new sqlite3.Database(DB_PATH);
    return new Promise((resolve) => {
        db.get(
            `SELECT o.id, o.status, o.total_price_lkr, o.order_date, o.shipping_address, o.payment_method, u.full_name
       FROM orders o
       JOIN users u ON o.user_id = u.id
       WHERE o.id = ? AND u.phone = ?`,
            [order_id, phone],
            (err, row) => {
                db.close();
                if (err || !row) {
                    return resolve('Sorry, no order found with that ID and phone number. Please double-check your order ID and phone, or reply "list my orders" to see your recent orders.');
                }
                const order = row as {
                    id: number;
                    status: string;
                    full_name: string;
                    total_price_lkr: number;
                    order_date: string;
                    shipping_address: string;
                    payment_method: string;
                };
                resolve(
                    `Order ID: ${order.id}\nStatus: ${order.status}\nName: ${order.full_name}\nTotal: LKR ${order.total_price_lkr}\nDate: ${order.order_date}\nAddress: ${order.shipping_address}\nPayment: ${order.payment_method}`
                );
            }
        );
    });
}
