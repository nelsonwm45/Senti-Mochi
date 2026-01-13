import apiClient from '../apiClient';

export interface SentimentResult {
    sentiment: 'positive' | 'neutral' | 'negative';
    confidence: number;
    reasoning: string;
}

export interface ArticleForSentiment {
    id: string;
    title: string;
    company: string;
    description?: string;
    content?: string;
    url?: string;
    source?: string;
}

export const sentimentApi = {
    /**
     * Analyze sentiment for multiple articles
     */
    async analyzeBatch(articles: ArticleForSentiment[]): Promise<Record<string, SentimentResult>> {
        const { data } = await apiClient.post<Record<string, SentimentResult>>(
            '/api/v1/sentiment/analyze',
            { articles }
        );
        return data;
    },

    /**
     * Analyze sentiment for a single article
     */
    async analyzeSingle(article: ArticleForSentiment): Promise<SentimentResult> {
        const { data } = await apiClient.post<SentimentResult>(
            '/api/v1/sentiment/analyze-single',
            article
        );
        return data;
    }
};
