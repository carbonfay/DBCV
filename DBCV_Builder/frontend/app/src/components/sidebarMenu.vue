<template>
  <div class="sidebar-menu">
    <ul>
      <li
        v-for="item in filteredMenuItems"
        :key="item.name"
        :class="{ active: route.path === item.path }"
      >
        <router-link :to="item.path">{{ item.name }}</router-link>
      </li>
    </ul>
    <div class="bottom-buttons">
      <a class="documentation" target="_blank" href="https://gitverse.ru/carbonfay/DBCV/wiki">
        <DocumentationIcon class="documentation-icon" />
        Документация
      </a>
      <button @click="handleLogout">
        <ExitIcon class="icon" style="width: 11px" />
        {{ currentUser ? `${currentUser.first_name} ${currentUser.last_name}` : 'Anonymous' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore, useUsersStore } from '@/stores'; // импорт сторов
import { ExitIcon, DocumentationIcon } from '@/components/icons'; // импорт иконок

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const usersStore = useUsersStore();

const currentUser = ref(null);
const isAdmin = ref(false);
const menuItems = ref([
  { name: 'Агенты', path: '/bots' },
  { name: 'Каналы', path: '/channels' },
  { name: 'Виджеты', path: '/widgets' },
  { name: 'Реквесты', path: '/requests' },
  { name: 'Шаблоны', path: '/templates', adminOnly: true },
]);

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

const filteredMenuItems = computed(() => {
  return menuItems.value.filter((item) => {
    return isAdmin.value || !item?.adminOnly;
  });
});

const loadCurrentUser = async () => {
  const userData = localStorage.getItem('users');
  if (userData) {
    const parsedData = JSON.parse(userData);
    currentUser.value = parsedData.currentUser;
    isAdmin.value = currentUser.value?.role === 'ADMIN';
  }
};

onMounted(() => {
  loadCurrentUser();
});
</script>

<style scoped>
.sidebar-menu {
  display: flex;
  flex-direction: column;
  background-color: rgba(49, 49, 49, 1);
  padding: 20px 0;
  height: 100vh;
  min-width: 300px;
  overflow: auto;
  position: sticky;
  top: 0;
}

.sidebar-menu li {
  border-bottom: 1px solid rgba(116, 116, 116, 1);
}

.sidebar-menu li a {
  display: block;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 13px 20px;
  color: #fff;
}

.sidebar-menu .documentation {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 13px 20px;
  margin-top: auto;
}

.sidebar-menu li a:hover {
  text-decoration: underline;
}

.sidebar-menu li:hover {
  background-color: #444;
}

.sidebar-menu li.active {
  background-color: #444;
}

.sidebar-menu button {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 20px 0;
}

.bottom-buttons {
  display: grid;
  margin-top: auto;
  gap: 4px;
}

.documentation-icon {
  fill: white;
  height: auto;
  width: 16px;
  position: relative;
  top: 3px;
  margin-right: 2px;
}
</style>
