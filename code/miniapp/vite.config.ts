import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  css: {
    preprocessorOptions: {
      scss: {
        // 全局注入设计变量，所有组件可直接使用
        additionalData: `@import "@/styles/variables.scss";`,
      },
    },
  },
})
