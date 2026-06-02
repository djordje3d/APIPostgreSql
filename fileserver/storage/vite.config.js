import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 9009,
    open: true,
    cors: { 
      origin: [
        'http://localhost:5173',   // Vue dashboard
        'http://localhost:3000',   // React frontend
        'http://127.0.0.1:5173',
        'http://127.0.0.1:3000',
      ],
      methods: ['GET', 'HEAD', 'OPTIONS'],
    },
  },
  build: {
    outDir: 'dist',
  },
});
