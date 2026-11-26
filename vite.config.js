import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    plugins: [react(), tailwindcss()],
    server: {
        // Optional dev proxy. The backend currently has no CORS middleware, so
        // set VITE_API_BASE_URL=/api in .env.local to route requests through
        // this proxy instead of calling http://127.0.0.1:8000 cross-origin.
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ''),
            },
        },
    },
})
