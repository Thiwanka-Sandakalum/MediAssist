// OrderSessionManager: Tracks and validates order state for each user session
import { PlaceOrderParams } from '../tools/order.tool';

export type OrderField = keyof PlaceOrderParams;
export const REQUIRED_ORDER_FIELDS: OrderField[] = [
    'drug_name',
    'quantity',
    'user_name',
    'address',
    'phone',
    'payment_method',
];

export interface OrderSession {
    fields: Partial<PlaceOrderParams>;
    confirmed: boolean;
}

export class OrderSessionManager {
    private sessions: Map<string, OrderSession> = new Map();

    getSession(userId: string): OrderSession {
        if (!this.sessions.has(userId)) {
            this.sessions.set(userId, { fields: {}, confirmed: false });
        }
        return this.sessions.get(userId)!;
    }

    updateField(userId: string, field: OrderField, value: any) {
        const session = this.getSession(userId);
        session.fields[field] = value;
        session.confirmed = false;
    }

    getMissingFields(userId: string): OrderField[] {
        const session = this.getSession(userId);
        return REQUIRED_ORDER_FIELDS.filter(f => !session.fields[f]);
    }

    setConfirmed(userId: string, confirmed: boolean) {
        const session = this.getSession(userId);
        session.confirmed = confirmed;
    }

    isConfirmed(userId: string): boolean {
        return this.getSession(userId).confirmed;
    }

    clear(userId: string) {
        this.sessions.delete(userId);
    }
}
