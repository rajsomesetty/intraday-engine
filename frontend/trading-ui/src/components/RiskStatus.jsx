import { useEffect, useState } from "react";
import api from "../api";

export default function RiskStatus() {

  const [risk, setRisk] = useState(null);

  const loadRisk = async () => {

    try {

      const res = await api.get("/risk/status/1");
      setRisk(res.data);

    } catch (err) {

      console.error("Failed to load risk", err);

    }

  };

  useEffect(() => {

    loadRisk();

    const interval = setInterval(loadRisk, 3000);

    return () => clearInterval(interval);

  }, []);

  if (!risk) return <div className="panel">Loading risk...</div>;

  return (

    <div className="panel">

      <div className="panel-title">Risk Dashboard</div>

      <table>

        <tbody>

          <tr>
            <td>Equity</td>
            <td>{risk.equity}</td>
          </tr>

          <tr>
            <td>Daily PnL</td>
            <td
              className={
                risk.daily_pnl >= 0
                  ? "metric-positive"
                  : "metric-negative"
              }
            >
              {risk.daily_pnl}
            </td>
          </tr>

          <tr>
            <td>Exposure</td>
            <td>{risk.exposure}</td>
          </tr>

          <tr>
            <td>Open Positions</td>
            <td>{risk.open_positions}</td>
          </tr>

          <tr>
            <td>Trading Enabled</td>
            <td
              className={
                risk.trading_enabled
                  ? "metric-positive"
                  : "metric-negative"
              }
            >
              {risk.trading_enabled ? "YES" : "NO"}
            </td>
          </tr>

        </tbody>

      </table>

    </div>

  );

}
