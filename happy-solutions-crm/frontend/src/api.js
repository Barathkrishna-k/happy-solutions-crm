import axios from "axios";

// Replace with your deployed backend API base URL
const BASE_URL = 'https://happy-solutions-crm.onrender.com';


const api = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: false
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

