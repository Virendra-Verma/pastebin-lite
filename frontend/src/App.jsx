import { useState } from "react";
import "./App.css";

function App() {
  const [content, setContent] = useState("");
  const [url, setUrl] = useState("");

  async function createPaste() {
    const res = await fetch("/api/pastes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });

    const data = await res.json();
    setUrl(data.url);
  }

  return (
    <div className="page">
      <div className="card">
        <h1>🔥 Pastebin Lite</h1>

        <textarea
          placeholder="Paste your text here..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />

        <button onClick={createPaste}>Create Paste</button>

        {url && (
          <p className="result">
            Share link:
            <a href={url} target="_blank">{url}</a>
          </p>
        )}
      </div>
    </div>
  );
}

export default App;
