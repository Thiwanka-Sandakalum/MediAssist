import fs from 'fs';
import path from 'path';

const CHAT_LOG_DIR = path.resolve(process.cwd(), 'chat_logs');
if (!fs.existsSync(CHAT_LOG_DIR)) {
    fs.mkdirSync(CHAT_LOG_DIR);
}

export interface ChatLogEntry {
    timestamp: string;
    userId: string;
    userMessage: string;
    botResponse: string;
    functionCalls?: Array<{ name: string; args: any; result: string }>;
    duration: number;
}

export class ChatLogger {
    private static getLogFilePath(userId: string): string {
        const date = new Date().toISOString().split('T')[0];
        return path.join(CHAT_LOG_DIR, `${userId}_${date}.jsonl`);
    }

    static logInteraction(entry: ChatLogEntry): void {
        const logFile = this.getLogFilePath(entry.userId);
        const logLine = JSON.stringify(entry) + '\n';
        fs.appendFileSync(logFile, logLine);
    }

    static getConversationHistory(userId: string, date?: string): ChatLogEntry[] {
        const targetDate = date || new Date().toISOString().split('T')[0];
        const logFile = path.join(CHAT_LOG_DIR, `${userId}_${targetDate}.jsonl`);

        if (!fs.existsSync(logFile)) {
            return [];
        }

        const lines = fs.readFileSync(logFile, 'utf-8').trim().split('\n');
        return lines.map(line => JSON.parse(line));
    }
}
