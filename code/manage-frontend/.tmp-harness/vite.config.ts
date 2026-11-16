import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
export default defineConfig({ root: __dirname, base: './', plugins: [vue()], resolve: { alias: { '@': resolve(__dirname, '../src') } }, build: { outDir: resolve(__dirname, 'out'), emptyOutDir: true } })
