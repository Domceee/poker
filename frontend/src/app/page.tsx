"use client";
import { useState, useEffect } from "react";
import { startGame, playerAction } from "./api";

export default function Home() {
  const[log, setLog] = useState<string[]>([]);
  const[history, setHistory] = useState<string[]>([]);

  // useEffect(() => {
  //   getHistory().then((response) => {
  //     setHistory(response.data || []);
  //   });
  // }, []);

  const handleAction = async (action: string, amount?: number) => {
    try {
      const response = await playerAction(action, amount);
      setLog((prevLog) => [...prevLog, response.data.message]);
    } catch (error) {
      console.error("Error performing action:", error);
    }
  };

  const handleStart = async () => {
    try {
      const response = await startGame();
      setLog((prevLog) => [
        ...prevLog,
        `${(response.data.log || []).join("\n")}`,
      ]);
    } catch (error) {
      console.error("Error starting game:", error);
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
          <button className="px-10 py-2 bg-gray-300 rounded text-black border-2 border-black">Apply</button>
          <button className="px-10 py-2 bg-red-400 rounded text-black border-2 border-black">Reset</button>
        </div>
        <div className="h-80 overflow-y-auto border p-2 mb-4">
          {log.map((entry, index) => (
            <div key={index} className="text-black">{entry}</div>
          ))}
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("fold")}>Fold</button>
          <button className="px-4 py-2 bg-green-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("check")}>Check</button>
          <button className="px-4 py-2 bg-green-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("call")}>Call</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">-</button>
          <button className="px-4 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("bet", 20)}>Bet 20</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">+</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">-</button>
          <button className="px-4 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("raise", 40)}>Raise 40</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">+</button>
          <button className="px-4 py-2 bg-red-500 rounded text-black hover:bg-gray-300"
          onClick={() => handleAction("allin")}>ALL IN</button>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-bold mb-2 text-black">Hand History</h2>
          <div className="h-96 overflow-y-auto border p-2">
            {history.map((entry, index) => (
              <div key={index} className="text-black">{entry}</div>
            ))}
          </div>
      </section>
    </main>
  );
}

// "use client";
// import { useState } from "react";

// export default function Home() {
//   const [handId, setHandId] = useState<string | null>(null);
//   const [log, setLog] = useState<string[]>([]);

//   const startGame = async () => {
//     const res = await fetch("http://localhost:8000/game/start", { method: "POST" });
//     const data = await res.json();
//     setHandId(data.hand_id);
//     setLog([`Game started: ${data.hand_id}`]);
//   };

//   const sendAction = async (action: string) => {
//     if (!handId) {
//       setLog((l) => [...l, "Start a game first!"]);
//       return;
//     }
//     const res = await fetch(`http://localhost:8000/game/action/${handId}?action=${action}`, { method: "POST" });
//     const data = await res.json();
//     setLog((l) => [...l, `Action: ${action}`]);
//   };

//   return (
//     <main className="flex flex-col items-center p-6">
//       <h1 className="text-2xl font-bold">Poker Frontend</h1>

//       <button onClick={startGame} className="m-2 p-2 bg-blue-500 text-white rounded">
//         Start Game
//       </button>

//       <div className="flex gap-2 mt-4">
//         <button onClick={() => sendAction("fold")} className="p-2 bg-gray-500 text-white rounded">Fold</button>
//         <button onClick={() => sendAction("check")} className="p-2 bg-gray-500 text-white rounded">Check</button>
//         <button onClick={() => sendAction("call")} className="p-2 bg-gray-500 text-white rounded">Call</button>
//         <button onClick={() => sendAction("bet 20")} className="p-2 bg-green-500 text-white rounded">Bet 20</button>
//         <button onClick={() => sendAction("raise 40")} className="p-2 bg-green-500 text-white rounded">Raise 40</button>
//         <button onClick={() => sendAction("all in")} className="p-2 bg-red-500 text-white rounded">All In</button>
//       </div>

//       <div className="mt-6 w-full max-w-lg bg-gray-100 p-4 rounded">
//         <h2 className="font-bold">Game Log</h2>
//         <ul>
//           {log.map((entry, idx) => (
//             <li key={idx}>{entry}</li>
//           ))}
//         </ul>
//       </div>
//     </main>
//   );
// }
