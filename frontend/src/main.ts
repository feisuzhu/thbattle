import '@/assets/scss/main.scss'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createClient, definePlugin, defaultPlugins } from 'villus'
import msgpack from "@msgpack/msgpack";

import App from './App.vue'
import router from './router'

const authPlugin = definePlugin(({ opContext }) => {
  const token = localStorage['token'];
  if (token) {
    opContext.headers.Authorization = `Bearer ${localStorage['token']}`;
  }
})
const msgpackPlugin = definePlugin(({ afterQuery, opContext, operation }) => {
  opContext.headers.ContentType = "application/msgpack";
  opContext.headers.Accept = "application/msgpack";
  opContext.body = msgpack.encode({ query: operation.query, variables: operation.variables });

  afterQuery(rslt => {
    rslt.data = msgpack.decode(rslt.data);
  })
})

const client = createClient({
  url: import.meta.env.FARM_METASERVICE_URL,
  cachePolicy: 'cache-first',
  use: [authPlugin, msgpackPlugin, ...defaultPlugins()]
})
const pinia = createPinia()

const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(client)

app.mount('#app')
