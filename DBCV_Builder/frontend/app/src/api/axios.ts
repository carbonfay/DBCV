import axios, { type AxiosInstance, type AxiosError } from 'axios';
import { useAuthStore } from '@/stores';
// @ts-ignore
import notyf from '@/plugins/notyf';
import router from '@/router';

const BASE_API_URL = 'http://localhost:8003/api/v1';
export const WEBSOCKET_BASE_URL = 'ws://localhost:8003/ws/channel';

// HTTP статусы
const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
} as const;

// Сообщения об ошибках
const ERROR_MESSAGES = {
  INSUFFICIENT_PRIVILEGES: "The user doesn't have enough privileges.",
  NETWORK_ERROR: 'Network Error',
  DEFAULT_ERROR: 'Ошибка!',
  INSUFFICIENT_RIGHTS: 'Недостаточно прав!',
} as const;

interface ApiErrorResponse {
  detail?: string;
  message?: string;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_API_URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

// Глобальный обработчик ошибок
export const safeApiCall = async (apiCall: Promise<any>) => {
  return apiCall
    .then((response) => response)
    .catch((error) => {
      console.error('SafeApiCall Error:', error);
      return null;
    });
};

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    const errorMessage = error.response?.data || ERROR_MESSAGES.NETWORK_ERROR;
    console.error('API Error:', errorMessage);

    if (
      typeof errorMessage === 'object' &&
      errorMessage.detail === ERROR_MESSAGES.INSUFFICIENT_PRIVILEGES
    ) {
      notyf.error(ERROR_MESSAGES.INSUFFICIENT_RIGHTS);
      throw error;
    }

    if (error.response?.status === HTTP_STATUS.UNAUTHORIZED) {
      console.log('Переход на страницу авторизации');
      localStorage.removeItem('accessToken');
      router.push('/login');
    } else if (error.response?.status === HTTP_STATUS.FORBIDDEN) {
      notyf.error(ERROR_MESSAGES.INSUFFICIENT_RIGHTS);
    } else {
      notyf.error(ERROR_MESSAGES.DEFAULT_ERROR);
    }

    throw error;
  }
);

apiClient.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  const token = authStore.accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
export const BASE_WEBSOCKET_URL = WEBSOCKET_BASE_URL;
