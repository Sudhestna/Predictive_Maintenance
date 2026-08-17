export interface ChatMessage {

    id: number;

    sender: 'user' | 'assistant';

    response: string;

    loading: boolean;

    streaming: boolean;

    timestamp: Date;

    chunks?: string[];

    filePath?: string;

    audioPath?: string;

    sources?: string[];

    isLatest?: boolean;

    feedbackSubmitted?: boolean;
    
    feedbackOpen?: boolean;
}