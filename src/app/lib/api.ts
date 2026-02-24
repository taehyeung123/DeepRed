// API Base URL
// Production (Vercel): empty string → same-origin requests proxied via vercel.json rewrites
// Development: localhost:8000 direct connection
export const API_BASE = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:8000');
