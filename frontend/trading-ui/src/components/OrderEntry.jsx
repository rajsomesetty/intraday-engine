import { useState } from "react";
import api from "../api";

export default function OrderEntry() {

  const [symbol, setSymbol] = useState("RELIANCE");
  const [qty, setQty] = useState(1);
  const [price, setPrice] = useState(500);
  const [side, setSide] = useState("BUY");

  const submit = async () => {

    try {

      await api.post("/orders", {
        account_id: 1,
        symbol: symbol,
        quantity: Number(qty),
        price: Number(price),
        side: side,
        idempotency_key: Date.now().toString()
      });

      alert("Order placed");

    } catch (e) {

      alert(e.response?.data?.detail || "Order failed");

    }

  };

  return (

    <div className="panel">

      <div className="panel-title">Order Entry</div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "8px"
        }}
      >

        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Symbol"
        />

        <input
          type="number"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
        />

        <input
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />

        <div
          style={{
            display: "flex",
            gap: "8px"
          }}
        >

          <select
            value={side}
            onChange={(e) => setSide(e.target.value)}
          >
            <option>BUY</option>
            <option>SELL</option>
          </select>

          <button onClick={submit}>
            Place Order
          </button>

        </div>

      </div>

    </div>

  );

}
