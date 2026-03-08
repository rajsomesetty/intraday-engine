import { useEffect, useState } from "react";
import api from "../api";

export default function Trades() {

  const [trades, setTrades] = useState([]);

  const loadTrades = async () => {
    try {
      const res = await api.get("/trades/");
      setTrades(res.data);
    } catch (err) {
      console.error("Failed to load trades", err);
    }
  };

  useEffect(() => {
    loadTrades();
  }, []);

  return (
    <div>
      <h2>Trades</h2>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Price</th>
          </tr>
        </thead>

        <tbody>
          {trades.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.symbol}</td>
              <td>{t.status}</td>
              <td>{t.quantity}</td>
              <td>{t.entry_price}</td>
            </tr>
          ))}
        </tbody>
      </table>

    </div>
  );
}
