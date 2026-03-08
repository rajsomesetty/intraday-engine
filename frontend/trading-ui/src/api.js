import axios from "axios";
import { API_BASE } from "./config";

const api = axios.create({
  baseURL: "/api",
});

export default api;

export const getSystemHealth = async () => {
  const res = await axios.get(`${API_BASE}/system/health`);
  return res.data;
};

export const getTrades = async () => {
  const res = await axios.get(`${API_BASE}/trades/`);
  return res.data;
};

export const getPositions = async () => {
  const res = await axios.get(`${API_BASE}/positions/`);
  return res.data;
};
