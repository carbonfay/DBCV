import { createApp } from 'vue';
import { createPinia } from 'pinia';
import '@/assets/styles.css';
import components from '@/components/ui';
import directives from '@/directives';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';

import App from '@/App.vue';
import router from '@/router';
import '@fortawesome/fontawesome-free/css/all.css';

const app = createApp(App);
const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);

components.forEach((component) => {
  app.component(component.name as string, component);
});

directives.forEach((directive) => {
  app.directive(directive.name, directive.value);
});

app.use(pinia);
app.use(router);

app.mount('#app');
