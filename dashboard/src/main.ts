import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/index.css'
import './assets/icom/style.css'
import './styles/zindex.css'

const app = createApp(App)
app.use(router)
app.mount('#app')
