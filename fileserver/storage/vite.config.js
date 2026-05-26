import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 9009,
    open: true,
  },
  build: {
    outDir: 'dist',
  },
});
