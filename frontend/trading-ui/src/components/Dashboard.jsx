import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE } from "../config";

export default function Dashboard() {

  const [health, setHealth] = useState(null);

  const load = () => {
    axios.get(`${API_BASE}/system/health`)
      .then(res => setHealth(res.data));
  };

  useEffect(() => {

    load();
    const t = setInterval(load, 5000);

    return () => clearInterval(t);

  }, []);

  if (!health) return <div className="panel">Loading...</div>;

  return (

    <div className="panel">

      <div className="panel-title">System Dashboard</div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5,1fr)",
          gap: "12px"
        }}
      >

        <div>
          <b>Redis</b>
          <div className="metric-positive">{health.redis}</div>
        </div>

        <div>
          <b>Postgres</b>
          <div className="metric-positive">{health.postgres}</div>
        </div>

        <div>
          <b>Kill Switch</b>
          <div className="metric-neutral">
            {health.kill_switch ? "DISABLED" : "ACTIVE"}
          </div>
        </div>

        <div>
          <b>Tick Queue</b>
          <div className="metric-neutral">{health.tick_queue_depth}</div>
        </div>

        <div>
          <b>Execution Queue</b>
          <div className="metric-neutral">{health.execution_queue_depth}</div>
        </div>

      </div>

    </div>

  );

}
