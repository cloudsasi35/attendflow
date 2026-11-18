import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/tailwind.css'
import { initTelemetry, recordBrowserError } from './telemetry'

initTelemetry()

const app = createApp(App)

app.config.errorHandler = (err, _instance, info) => {
  recordBrowserError(err, `vue:${info}`)
  console.error(err)
}

app.use(createPinia())
app.use(router)

app.mount('#app')
