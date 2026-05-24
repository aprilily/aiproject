import { useState } from "react";
import LandingPage from "./components/LandingPage";
import ChatLayout from "./components/ChatLayout";
import "./App.css";

function App() {
  const [started, setStarted] = useState(false);

  return (
    <div className="app">
      {!started ? (
        <LandingPage onStart={() => setStarted(true)} />
      ) : (
        <ChatLayout />
      )}
    </div>
  );
}

export default App;
