import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
export default defineConfig({ root: __dirname, base: './', plugins: [vue(), createSvgIconsPlugin({ iconDirs: [resolve(__dirname, '../src/icons')], symbolId: 'icon-[name]' })], resolve: { alias: [
  { find: /^@\/api$/, replacement: resolve(__dirname, 'stub-api.ts') },
  { find: 'vue-router', replacement: resolve(__dirname, 'stub-router.ts') },
  { find: '@', replacement: resolve(__dirname, '../src') } ] }, build: { outDir: resolve(__dirname, 'out'), emptyOutDir: true } })
