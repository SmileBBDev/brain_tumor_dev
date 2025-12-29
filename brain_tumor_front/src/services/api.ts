import axios from 'axios';

// 비동기 api 통신 기본 세팅
// Axios 인스턴스 생성
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  withCredentials: true, // 쿠키 포함 (refresh token 등)
});

// 요청 인터셉터
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    // 반드시 Bearer 뒤에 공백 필요
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 응답 인터셉터
let isRefreshing = false;
let refreshQueue: (() => void)[] = [];

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          // refresh 요청
          const res = await api.post("/auth/refresh/");
          localStorage.setItem("accessToken", res.data.access);
          localStorage.setItem("refreshToken", res.data.refresh);

          // 대기 중인 요청 재시도
          refreshQueue.forEach((cb) => cb());
          refreshQueue = [];
        } catch {
          localStorage.clear();
          window.location.href = "/login";
          return Promise.reject(error);
        } finally {
          isRefreshing = false;
        }
      }

      return new Promise((resolve) => {
        refreshQueue.push(() => resolve(api(original)));
      });
    }

    return Promise.reject(error);
  }
);