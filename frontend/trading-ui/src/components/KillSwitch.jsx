import axios from "axios";
import { API_BASE } from "../config";

export default function KillSwitch(){

  const enable = () => {
    axios.post(`${API_BASE}/system/kill-switch/enable`)
  }

  const disable = () => {
    axios.post(`${API_BASE}/system/kill-switch/disable`)
  }

  return (

    <div>

      <h2>Trading Control</h2>

      <button onClick={enable}>
        Enable Trading
      </button>

      <button onClick={disable}>
        Disable Trading
      </button>

    </div>
  )
}
