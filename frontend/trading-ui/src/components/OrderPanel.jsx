import { useState } from "react";
import axios from "axios";
import { API_BASE } from "../config";

export default function OrderPanel(){

  const [symbol,setSymbol] = useState("RELIANCE")
  const [qty,setQty] = useState(1)
  const [price,setPrice] = useState(2500)

  const submit = async () => {

    await axios.post(`${API_BASE}/orders`,{
      account_id:1,
      symbol:symbol,
      quantity:parseInt(qty),
      price:parseFloat(price),
      side:"BUY",
      idempotency_key:Date.now().toString()
    })

  }

  return(

    <div>

      <h2>Manual Order</h2>

      <input
        value={symbol}
        onChange={e=>setSymbol(e.target.value)}
        placeholder="Symbol"
      />

      <input
        value={qty}
        onChange={e=>setQty(e.target.value)}
        placeholder="Quantity"
      />

      <input
        value={price}
        onChange={e=>setPrice(e.target.value)}
        placeholder="Price"
      />

      <button onClick={submit}>
        BUY
      </button>

    </div>

  )
}
