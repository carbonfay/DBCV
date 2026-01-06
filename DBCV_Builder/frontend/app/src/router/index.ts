import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import notyf from '@/plugins/notyf';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/channelsPage.vue'),
    meta: { title: 'DBCV', requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/loginPage.vue'),
    meta: { title: 'DBCV', requiresAuth: false },
  },
  {
    path: '/channels',
    name: 'channelsPage',
    component: () => import('@/views/channelsPage.vue'),
    meta: { title: 'DBCV', requiresAuth: true },
  },
  {
    path: '/bot/:id',
    name: 'botPage',
    component: () => import('@/views/homePage.vue'),
    props: true,
    meta: { title: 'DBCV', requiresAuth: true },
  },
  {
    path: '/bots',
    name: 'botsPage',
    component: () => import('@/views/botsPage.vue'),
    meta: { title: 'DBCV', requiresAuth: true },
  },
  {
    path: '/widgets',
    name: 'widgetsPage',
    component: () => import('@/views/widgetsPage.vue'),
    meta: { title: 'DBCV', requiresAuth: true },
  },
  {
    path: '/requests',
    name: 'requestsPage',
    component: () => import('@/views/requestsPage.vue'),
    meta: { title: 'DBCV', requiresAuth: true },
  },
  {
    path: '/templates',
    name: 'templatesPage',
    component: () => import('@/views/templatesPage.vue'),
    meta: { title: 'DBCV', requiresAuth: true, requiresAdmin: true },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

function getCurrentUser() {
  try {
    const userData = localStorage.getItem('users');
    if (userData) {
      const data = JSON.parse(userData);
      return data.currentUser || null;
    }
    return null;
  } catch (error) {
    console.error('Error parsing user data:', error);
    return null;
  }
}

function isAdmin(): boolean {
  const user = getCurrentUser();
  return user?.role === 'ADMIN';
}

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('accessToken');

  if (to.meta.title) {
    window.document.title = to.meta.title as string;
  }

  if (to.name === 'Login' && isAuthenticated) {
    next({ path: '/channels' });
    return;
  }

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ path: '/login' });
    return;
  }

  if (to.meta.requiresAdmin && !isAdmin()) {
    notyf.error('Недостаточно прав для доступа к этой странице');

    next(from.path !== '/' ? from.path : '/channels');
    return;
  }

  next();
});

export default router;
