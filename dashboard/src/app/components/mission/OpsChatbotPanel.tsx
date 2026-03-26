import { useState } from "react";
import { Bot, Send, Loader2 } from "lucide-react";

import { API_BASE } from "../../../config/api";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: { source: string; reference: string }[];
};

type AskResponse = {
  session_id: string;
  answer: string;
  citations: { source: string; reference: string }[];
  quality_score: number;
  tool_trace: string[];
};

interface OpsChatbotPanelProps {
  incidentId?: string | null;
}

export function OpsChatbotPanel({ incidentId }: OpsChatbotPanelProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "I am your Mission Control assistant. Ask things like: 'What should we do next?' or 'Do we have pending approvals?'",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chatbot/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          incident_id: incidentId || undefined,
        }),
      });
      if (!response.ok) {
        throw new Error(`Chatbot error (${response.status})`);
      }
      const data: AskResponse = await response.json();
      if (!sessionId) setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `${data.answer}\n\n(quality: ${data.quality_score.toFixed(2)} | tools: ${data.tool_trace.join(", ")})`,
          citations: data.citations,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `I could not process that request right now: ${
            error instanceof Error ? error.message : "unknown error"
          }`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
      <div className="flex items-center gap-2 mb-3">
        <Bot className="w-4 h-4 text-blue-300" />
        <h3 className="text-sm font-semibold text-white">Ops Chatbot</h3>
      </div>

      <div className="h-64 overflow-y-auto space-y-3 pr-1">
        {messages.map((message, index) => (
          <div key={index} className={message.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[90%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-200 border border-slate-700"
              }`}
            >
              {message.content}
            </div>
            {message.citations && message.citations.length > 0 && (
              <div className="mt-1 text-xs text-slate-500 space-x-2">
                {message.citations.map((citation, i) => (
                  <span key={`${citation.source}-${i}`} className="inline-block">
                    {citation.source}: {citation.reference}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") handleSend();
          }}
          placeholder="Ask about top incident, approvals, next action..."
          className="flex-1 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : <Send className="w-4 h-4 text-white" />}
        </button>
      </div>
    </div>
  );
}
