import { useEffect, useState } from "react";
import api from "../api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer
} from "recharts";

export default function EquityChart() {

  const [data, setData] = useState([]);

  const loadEquity = async () => {
    try {

      const res = await api.get("/analytics/equity/1");

      setData(res.data);

    } catch (err) {

      console.error("Failed to load equity history", err);

    }
  };

  useEffect(() => {

    loadEquity();

    const interval = setInterval(loadEquity, 5000);

    return () => clearInterval(interval);

  }, []);

  return (

    <div>

      <h2>Equity Curve</h2>

      <ResponsiveContainer width="100%" height={300}>

        <LineChart data={data}>

          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="time" />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="equity"
            stroke="#4cafef"
            strokeWidth={2}
          />

        </LineChart>

      </ResponsiveContainer>

    </div>
  );
}
