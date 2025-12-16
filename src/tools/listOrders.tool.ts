import sqlite3 from 'sqlite3';
import path from 'path';

export const listOrdersByPhoneParams = {
    type: 'object',
    properties: {
        phone: {
            type: 'string',
            description: 'User phone number to list recent orders',
        },
    },
    required: ['phone'],
};

export const listOrdersByPhoneFunctionDeclaration = {
    name: 'list_orders_by_phone',
    description: 'List recent pharmacy orders for a user by phone number. Use this to help users track their recent orders if they forgot their order ID.',
    parameters: listOrdersByPhoneParams,
};

const DB_PATH = path.resolve(process.cwd(), 'pharmacy_sim.db');

export async function listOrdersByPhone(params: { phone: string }): Promise<string> {
    const { phone } = params;
    const db = new sqlite3.Database(DB_PATH);
    return new Promise((resolve) => {
        db.all(
            `SELECT o.id, o.status, o.total_price_lkr, o.order_date, o.shipping_address, o.payment_method
       FROM orders o
       JOIN users u ON o.user_id = u.id
       WHERE u.phone = ?
       ORDER BY o.order_date DESC
       LIMIT 5`,
            [phone],
            (err, rows) => {
                db.close();
                if (err || !rows || rows.length === 0) {
                    return resolve('No recent orders found for this phone number.');
                }
                const orders = rows.map((row: any) =>
                    `Order ID: ${row.id}\nStatus: ${row.status}\nTotal: LKR ${row.total_price_lkr}\nDate: ${row.order_date}\nAddress: ${row.shipping_address}\nPayment: ${row.payment_method}`
                );
                resolve('Recent orders:\n' + orders.join('\n---\n'));
            }
        );
    });
}
