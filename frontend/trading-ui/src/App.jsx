import TerminalLayout from "./components/TerminalLayout";

function App() {

  return (

    <div>

      <div
        style={{
          padding:"12px",
          borderBottom:"1px solid #2f3b55",
          marginBottom:"10px"
        }}
      >

        <h1 style={{margin:0}}>
          Intraday Trading Engine
        </h1>

      </div>

      <TerminalLayout/>

    </div>

  );

}

export default App;
