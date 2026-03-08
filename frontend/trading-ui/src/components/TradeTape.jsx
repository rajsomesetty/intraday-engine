import { useEffect, useState } from "react";

export default function TradeTape() {

  const [trades, setTrades] = useState([]);

  useEffect(() => {

    const ws = new WebSocket(`ws://${window.location.host}/ws/trades`);

    ws.onmessage = (msg) => {

      const trade = JSON.parse(msg.data);

      setTrades((prev) => [trade, ...prev.slice(0,20)]);

    };

    return () => ws.close();

  }, []);

  return (

    <div className="panel">

      <div className="panel-title">Live Trade Tape</div>

      {trades.map((t,i)=>(
        <div key={i}>

          {t.symbol} {t.side} {t.quantity} @ {t.price}

        </div>
      ))}

    </div>

  );
}
