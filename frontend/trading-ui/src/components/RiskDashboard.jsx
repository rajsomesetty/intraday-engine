import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE } from "../config";

export default function RiskDashboard() {

  const [risk, setRisk] = useState(null);

  const loadRisk = async () => {
    const res = await axios.get(`${API_BASE}/risk/status/1`);
    setRisk(res.data);
  };

  useEffect(() => {

    loadRisk();

    const interval = setInterval(loadRisk, 5000);

    return () => clearInterval(interval);

  }, []);

  if (!risk) return <div>Loading risk...</div>;

  return (

    <div>

      <h2>Risk Dashboard</h2>

      <div style={{display:"flex", gap:"40px"}}>

        <div>
          <h4>Equity</h4>
          <p>{risk.equity}</p>
        </div>

        <div>
          <h4>Daily PnL</h4>
          <p>{risk.daily_pnl}</p>
        </div>

        <div>
          <h4>Exposure</h4>
          <p>{risk.exposure}</p>
        </div>

        <div>
          <h4>Open Positions</h4>
          <p>{risk.open_positions}</p>
        </div>

        <div>
          <h4>Trading Enabled</h4>
          <p>{risk.trading_enabled ? "YES" : "NO"}</p>
        </div>

      </div>

    </div>

  );
}
