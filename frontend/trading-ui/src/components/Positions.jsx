import { useEffect, useState } from "react";
import { getPositions } from "../api";

export default function Positions() {

  const [positions, setPositions] = useState([]);

  const load = () => {
    getPositions().then(setPositions);
  };

  useEffect(() => {

    load();

    const t = setInterval(load, 3000);

    return () => clearInterval(t);

  }, []);

  return (

    <div className="panel">

      <div className="panel-title">Positions</div>

      <table style={{ width: "100%" }}>

        <thead>
          <tr>
            <th>Symbol</th>
            <th>Qty</th>
            <th>Entry</th>
            <th>PnL</th>
          </tr>
        </thead>

        <tbody>

          {positions.map((p, i) => {

            const ltp = p.entry_price; // placeholder until price feed used
            const pnl = (ltp - p.entry_price) * p.quantity;

            return (

              <tr key={i}>

                <td>{p.symbol}</td>

                <td>{p.quantity}</td>

                <td>{p.entry_price}</td>

                <td
                  className={
                    pnl >= 0 ? "pnl-positive" : "pnl-negative"
                  }
                >
                  {pnl.toFixed(2)}
                </td>

              </tr>

            );

          })}

        </tbody>

      </table>

    </div>

  );

}
