"use client";
import { use, useState } from "react";

export default function Home() {
  const[log, setLog] = useState<string[]>([]);
  const[history, setHistory] = useState<string[]>([]);

  const addLog = (msg: string) => setLog((prev) => [...prev, msg]);

  return (
    <main className="grid grid-cols-2 gap-4 p-4 min-h-screen bg-gray-100">

      <section className="bg-white p-4 rounded shadow">
        <h2 className="text-xl font-bold mb-2 text-black">Playing field log</h2>
        <div className="h-80 overflow-y-auto border p-2 mb-4">
          {log.map((entry, index) => (
            <div key={index} className="text-black">{entry}</div>
          ))}
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-500 rounded text-black hover:bg-gray-300"
          onClick={() => addLog("Player folds")}>Fold</button>
          <button className="px-4 py-2 bg-green-500 rounded text-black hover:bg-gray-300"
          onClick={() => addLog("Player checks")}>Check</button>
          <button className="px-4 py-2 bg-green-500 rounded text-black hover:bg-gray-300"
          onClick={() => addLog("Player calls")}>Call</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">-</button>
          <button className="px-4 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => addLog("Player bets 20")}>Bet 20</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">+</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">-</button>
          <button className="px-4 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300"
          onClick={() => addLog("Player raises 40")}>Raise 40</button>
          <button className="px-2 py-2 bg-yellow-500 rounded text-black hover:bg-gray-300">+</button>
          <button className="px-4 py-2 bg-red-500 rounded text-black hover:bg-gray-300">ALL IN</button>
        </div>
      </section>

      <section className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-bold mb-2 text-black">Hand History</h2>
          <div className="h-96 overflow-y-auto border p-2">

          </div>
      </section>
    </main>
  );
}
