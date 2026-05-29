import { useState } from "react";
import LandingPage from "./components/LandingPage";
import ChatLayout from "./components/ChatLayout";
import "./App.css";

function App() {
  const [started, setStarted] = useState(false);
  const [initialMessage, setInitialMessage] = useState(null);

  const handleStart = (message = null) => {
    if (message) {
      setInitialMessage(message);
    } else {
      setInitialMessage(null);
    }
    setStarted(true);
  };

  const handleGoHome = () => {
    setStarted(false);
    setInitialMessage(null);
  };

  return (
    <div className="app">
      {!started ? (
        <LandingPage onStart={handleStart} />
      ) : (
        <ChatLayout onGoHome={handleGoHome} initialMessage={initialMessage} />
      )}
    </div>
  );
}

export default App;

//