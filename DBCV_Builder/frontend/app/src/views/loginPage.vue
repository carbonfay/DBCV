<template>
  <div class="login-page">
    <div class="login-block">
      <h2>Авторизация</h2>
      <form @submit.prevent="handleLogin">
        <BaseInput
          type="text"
          required
          v-model="form.username"
          label="Логин"
          class="section-input"
          labelColor="rgb(44, 44, 44)"
          :error="v$.username.$error ? v$.username.$errors[0].$message : undefined"
        />

        <BaseInput
          type="password"
          required
          v-model="form.password"
          label="Пароль"
          class="section-input"
          labelColor="rgb(44, 44, 44)"
          :error="v$.password.$error ? v$.password.$errors[0].$message : undefined"
        />

        <BaseButton
          styleType="primary"
          size="medium"
          type="submit"
          :disabled="isLoading || v$.$invalid"
        >
          {{ isLoading ? 'Вход...' : 'Войти' }}
        </BaseButton>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
      <a class="forgot-password">Забыли пароль?</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore, useUsersStore } from '@/stores';
import { useVuelidate } from '@vuelidate/core';
import { loginRules } from '@/plugins/vuelidate';

const form = reactive({
  username: '',
  password: '',
});

const authStore = useAuthStore();
const usersStore = useUsersStore();
const router = useRouter();

const error = ref<string | null>(null);
const isLoading = ref(false);

const v$ = useVuelidate(loginRules, form);

const handleLogin = async () => {
  error.value = null;

  await v$.value.$validate();

  if (v$.value.$invalid) return;

  isLoading.value = true;

  const response = await authStore.login(form.username, form.password);

  if (response && response.data?.access_token) {
    await usersStore.readCurrentUser();
    router.push('/channels');
  } else {
    error.value = 'Неверный логин или пароль';
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  height: 100vh;
  background: rgb(40, 40, 40);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.login-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #fff;
  border-radius: 20px;
  padding: 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 1;
}

h2 {
  margin: 0 0 25px;
  color: rgb(44, 44, 44);
}

form {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  position: relative;
}

.section-input {
  margin: 0 0 15px;
  width: 100%;
}

.custom-button {
  margin: 15px 0 0;
  width: 100%;
}

.forgot-password {
  color: #667eea;
  text-decoration: none;
  margin: 15px 0 0;
  font-size: 12px;
  transition: color 0.2s ease;
}

.forgot-password:hover {
  color: #5a6fd8;
  text-decoration: underline;
}

.error {
  margin: 15px 0 0;
  color: #dc3545;
  font-size: 12px;
}

/* Анимации */
.login-block {
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
