import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from '@farmfe/core';

import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx'

export default defineConfig({
  plugins: ['@farmfe/plugin-sass'],
  vitePlugins: [vue(), vueJsx(),],
  compilation: {
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
  },
  // server: {
  //   proxy: {
  //     "/api": {
  //       target: process.env.FARM_METASERVICE_URL,
  //       changeOrigin: true,
  //       pathRewrite: (path: any) => path.replace(/^\/api/, ""),
  //     }
  //   }
  // }
});
