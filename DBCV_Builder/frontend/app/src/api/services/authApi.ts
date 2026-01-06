import apiClient, { safeApiCall } from '@/api/axios';

const authApi = {
  login(data: Record<string, unknown>) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(data)) {
      params.append(key, String(value));
    }

    return safeApiCall(
      apiClient.post('/login/access-token', params.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
    );
  },
};

export default authApi;
