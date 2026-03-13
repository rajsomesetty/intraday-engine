import axios from "axios";
import { API_BASE } from "./config";

/*
------------------------------------------------
Axios Client
------------------------------------------------
*/

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;

/*
------------------------------------------------
System APIs
------------------------------------------------
*/

export const getSystemHealth = async () => {
  const res = await api.get("/system/health");
  return res.data;
};

/*
------------------------------------------------
Trading APIs
------------------------------------------------
*/

export const getTrades = async () => {
  const res = await api.get("/trades/");
  return res.data;
};

export const getPositions = async () => {
  const res = await api.get("/positions/");
  return res.data;
};

/*
------------------------------------------------
Risk APIs
------------------------------------------------
*/

export const getRiskStatus = async (accountId) => {
  const res = await api.get(`/risk/status/${accountId}`);
  return res.data;
};

/*
------------------------------------------------
Equity Analytics
------------------------------------------------
*/

export const getEquityHistory = async (accountId) => {
  const res = await api.get(`/analytics/equity/${accountId}`);
  return res.data;
};

/*
------------------------------------------------
Kill Switch
------------------------------------------------
*/

export const enableTrading = async () => {
  const res = await api.post("/system/kill-switch/enable");
  return res.data;
};

export const disableTrading = async () => {
  const res = await api.post("/system/kill-switch/disable");
  return res.data;
};

/*
------------------------------------------------
WebSocket Helpers
------------------------------------------------
*/

export const connectTradeStream = (onMessage) => {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";

  const socket = new WebSocket(
    `${protocol}://${window.location.host}/ws/trades`
  );

  socket.onopen = () => {
    console.log("📡 Trade stream connected");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
  };

  socket.onclose = () => {
    console.warn("Trade stream disconnected");
  };

  return socket;
};
