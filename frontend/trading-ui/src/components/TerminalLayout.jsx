import GridLayout from "react-grid-layout";
import { useState, useEffect } from "react";

import Dashboard from "./Dashboard";
import RiskStatus from "./RiskStatus";
import EquityChart from "./EquityChart";
import OrderEntry from "./OrderEntry";
import Exposure from "./Exposure";
import Trades from "./Trades";
import Positions from "./Positions";
import TradeTape from "./TradeTape";
import KillSwitch from "./KillSwitch";

import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

export default function TerminalLayout() {

  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {

    const handleResize = () => {
      setWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);

  }, []);

  const layout = [

    { i: "system", x: 0, y: 0, w: 3, h: 2 },
    { i: "risk", x: 3, y: 0, w: 3, h: 2 },
    { i: "order", x: 6, y: 0, w: 3, h: 2 },
    { i: "kill", x: 9, y: 0, w: 3, h: 2 },

    { i: "equity", x: 0, y: 2, w: 8, h: 4 },
    { i: "exposure", x: 8, y: 2, w: 4, h: 4 },

    { i: "trades", x: 0, y: 6, w: 6, h: 4 },
    { i: "positions", x: 6, y: 6, w: 6, h: 4 },

    { i: "tape", x: 0, y: 10, w: 12, h: 3 }

  ];

  return (

    <GridLayout
      className="layout"
      layout={layout}
      cols={12}
      rowHeight={70}
      width={width}
      margin={[10,10]}
      isResizable={false}
    >

      <div key="system" className="panel">
        <Dashboard />
      </div>

      <div key="risk" className="panel">
        <RiskStatus />
      </div>

      <div key="order" className="panel">
        <OrderEntry />
      </div>

      <div key="kill" className="panel">
        <KillSwitch />
      </div>

      <div key="equity" className="panel">
        <EquityChart />
      </div>

      <div key="exposure" className="panel">
        <Exposure />
      </div>

      <div key="trades" className="panel">
        <Trades />
      </div>

      <div key="positions" className="panel">
        <Positions />
      </div>

      <div key="tape" className="panel">
        <TradeTape />
      </div>

    </GridLayout>

  );

}
