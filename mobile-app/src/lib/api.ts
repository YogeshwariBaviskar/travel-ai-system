import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({ baseURL: BASE_URL });

apiClient.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const api = {
  auth: {
    me: () => apiClient.get("/api/auth/me").then((r) => r.data),
  },
  trips: {
    list: () => apiClient.get("/api/trips/").then((r) => r.data),
    get: (id: string) => apiClient.get(`/api/trips/${id}`).then((r) => r.data),
    create: (data: object) => apiClient.post("/api/trips/", data).then((r) => r.data),
    delete: (id: string) => apiClient.delete(`/api/trips/${id}`),
    explain: (id: string) =>
      apiClient.post(`/api/trips/${id}/explain`).then((r) => r.data),
  },
};

export const WS_BASE = (process.env.EXPO_PUBLIC_API_URL || "ws://localhost:8000").replace("http", "ws");
