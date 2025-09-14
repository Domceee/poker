"use client";
import { useState, useEffect } from "react";
import { startGame, playerAction, getHistory, resetGame, applyStacks } from "./api";

export default function Home() {
  const[log, setLog] = useState<string[]>([]);
  const[history, setHistory] = useState<string[]>([]);
  const [gameId, setGameId] = useState<string | null>(null);
  const [lastLength, setLastLength] = useState(0);
  const [betAmount, setBetAmount] = useState(20);
  const [raiseAmount, setRaiseAmount] = useState(40);
  const [startingStack, setStartingStack] = useState(10000);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await getHistory();
      setHistory(response.data.hands || []);
    } catch (error) {
      console.error("Error loading history:", error);
    }
  };

  const handleAction = async (action: string, amount?: number) => {
    try {
      const response = await playerAction(action, amount);
      const actions = response.data.actions || [];
      const newEntries = actions.slice(lastLength);
      setLog((prevLog) => [
        ...prevLog,
        ...newEntries,
      ]);
      setLastLength(actions.length);

      if (response.data.finished) {
        await loadHistory();
        setGameId(null);
        setLastLength(0);
        setLog((prevLog) => [
          ...prevLog,
          ...(response.data.hands || [])
        ]);
      }
    } catch (error) {
      console.error("Error performing action:", error);
    }
  };

  const handleStart = async () => {
    try {
      const response = await startGame();
      const log = response.data.log || [];
      const newEntry = log.slice(lastLength);
      setLog((prevLog) => [
        ...prevLog,
        ...newEntry,
      ]);
      setLastLength(log.length);
    } catch (error) {
      console.error("Error starting game:", error);
    }
  };

  const handleReset = async() => {
    try {
      const response = await resetGame(startingStack);
      console.log(response.data.message);
      setLog([]);
      setLastLength(0);
      setGameId(null);
      setBetAmount(20);
      setRaiseAmount(40);
    } catch (error) {
        console.error("Failed to reset the game: ", error);
    }
  }

  const handleApply = async () => {
    try {
      const response = await applyStacks(startingStack);
      console.log(response.data.message);
      setLog((prev) => [...prev, `Stacks set to ${startingStack}`]);
    } catch (error) {
      console.error("Failed to apply stacks:", error);
      setLog((prev) => [...prev, "Failed to apply stacks"]);
    }
  };

  return (
    <main className="grid grid-cols-2 gap-4 p-4 min-h-screen bg-gray-100">

      <section className="bg-white p-4 rounded shadow">
        <div>
          <h2 className="text-xl font-bold mb-2 text-black">Playing field log</h2>
          <button className="mb-2 px-117 py-2 bg-red-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleStart()}>Start</button>
        </div>
        <div className="flex gap-2">
          <h2 className="text-black text-lg font-bold mb-3">Stacks</h2>
          <input type="number" value={startingStack} onChange={(e) => setStartingStack(parseInt(e.target.value) || 0)} className="border p-1 rounded w-24"/>
          <button className="px-10 py-2 bg-gray-300 rounded text-black border-2 border-black"
          onClick={() => handleApply()}>Apply</button>
          <button className="px-10 py-2 bg-red-400 rounded text-black border-2 border-black"
          onClick={() => handleReset()}>Reset</button>
        </div>
        <div className="h-80 overflow-y-auto border p-2 mb-4">
          {log.map((entry, index) => (
            <div key={index} className="text-black">{entry}</div>
          ))}
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("f")}>Fold</button>
          <button className="px-4 py-2 bg-green-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("x")}>Check</button>
          <button className="px-4 py-2 bg-green-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("c")}>Call</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => setBetAmount((prev) => Math.max(20, prev - 20))}>-</button>
          <button className="px-4 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("b", betAmount)}>Bet {betAmount}</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => setBetAmount((prev) => prev + 20)}>+</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => setRaiseAmount((prev) => Math.max(40, prev - 20))}>-</button>
          <button className="px-4 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("r", raiseAmount)}>Raise {raiseAmount}</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => setRaiseAmount((prev) => prev + 20)}>+</button>
          <button className="px-4 py-2 bg-red-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("allin")}>ALL IN</button>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-bold mb-2 text-black">Hand History</h2>
          <div className="h-200 overflow-y-auto border p-2">
            {history.map((entry, index) => (
              <div key={index} className="text-black font-mono text-xs mb-4 border-b pb-2">
                {entry.split('\n').map((line, lineIndex) => (
                  <div key={lineIndex}>{line}</div>
                ))}</div>
            ))}
          </div>
          <button 
            className="mt-2 px-4 py-2 bg-blue-500 rounded text-white hover:bg-blue-600"
            onClick={loadHistory}
          >Refresh History</button>
      </section>
    </main>
  );
}