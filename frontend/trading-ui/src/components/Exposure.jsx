import { useEffect, useState } from "react";
import api from "../api";

export default function Exposure() {

  const [positions, setPositions] = useState([]);

  const load = async () => {

    const res = await api.get("/positions/");
    setPositions(res.data);

  };

  useEffect(() => {

    load();

    const t = setInterval(load, 3000);

    return () => clearInterval(t);

  }, []);

  return (

    <div className="panel">

      <div className="panel-title">Exposure</div>

      {positions.map(p => {

        const exposure = p.quantity * p.entry_price;

        return (

          <div
            key={p.symbol}
            style={{ marginBottom: "12px" }}
          >

            <div
              style={{
                display: "flex",
                justifyContent: "space-between"
              }}
            >
              <span>{p.symbol}</span>
              <span>{exposure}</span>
            </div>

            <div
              className="exposure-bar"
              style={{
                width: exposure / 50
              }}
            />

          </div>

        )

      })}

    </div>

  );

}
