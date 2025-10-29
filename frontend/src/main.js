import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";
import { useAuthStore } from "./stores/auth";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);

// Hydrate user on refresh and start SSE
const auth = useAuthStore();
auth.verifyToken().catch(() => {});

app.mount("#app");
