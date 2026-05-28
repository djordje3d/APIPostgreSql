import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/index.ts";
import { i18n } from "./i18n.ts";
import "./styles/index.css";
import "./assets/icom/style.css";
import "./styles/zindex.css";

const app = createApp(App);
app.use(router);
app.use(i18n);
app.mount("#app");
