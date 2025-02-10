// API Konfiguration für das gesamte Frontend
export const API_CONFIG = {
    BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
    DEBUG: process.env.NODE_ENV === 'development'
};

// Logger für API-Aufrufe
export const debug = (...args: any[]) => {
    if (API_CONFIG.DEBUG) {
        console.log('[API]', ...args);
    }
};