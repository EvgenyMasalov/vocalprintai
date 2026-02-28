const API_URL = '/api';

export interface AdminClient {
    id: number;
    username: string;
    email: string;
    is_admin: boolean;
    created_at: string;
}

export interface AdminGeneration {
    filename: string;
    artist: string;
    timestamp: number;
}

export const adminService = {
    async getClients(): Promise<AdminClient[]> {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/admin/clients`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch clients');
        return response.json();
    },

    async getGenerations(): Promise<AdminGeneration[]> {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/admin/generations`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch generations');
        return response.json();
    },

    async uploadRagFile(file: File) {
        const token = localStorage.getItem('token');
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/admin/rag/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        if (!response.ok) throw new Error('Failed to upload RAG file');
        return response.json();
    }
};
