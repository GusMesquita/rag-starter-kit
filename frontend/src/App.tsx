import { type FormEvent, useEffect, useRef, useState } from "react";
import { ChatMessage, type Message } from "./components/ChatMessage";
import { TypingIndicator } from "./components/TypingIndicator";
import { askQuestion } from "./lib/api";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || pending) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setPending(true);
    setError(null);

    try {
      const response = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, sourcesUsed: response.sources_used },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex h-screen max-w-2xl flex-col px-4 sm:px-6">
      <header className="flex flex-col gap-1 border-b border-border/60 py-6">
        <h1 className="bg-gradient-to-r from-primary to-accent bg-clip-text text-2xl font-bold text-transparent">
          rag-starter-kit
        </h1>
        <p className="text-sm text-muted">Pergunte algo com base nos documentos ingeridos.</p>
      </header>

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto py-6">
        {messages.length === 0 && !pending && (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-center text-muted">
            <span className="text-3xl">💬</span>
            <p>Faça a primeira pergunta para começar.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <ChatMessage key={index} {...message} />
        ))}
        {pending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="mb-4 rounded-2xl border border-danger/40 bg-surface-raised px-4 py-3 text-sm text-danger">
          Falha: {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border/60 py-4">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Digite sua pergunta..."
          disabled={pending}
          className="flex-1 rounded-full border border-border bg-surface px-4 py-2.5 text-sm text-text outline-none transition-colors placeholder:text-faint focus:border-primary disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="rounded-full bg-gradient-to-br from-primary to-accent px-5 py-2.5 text-sm font-semibold text-white transition-transform enabled:hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Enviar
        </button>
      </form>
    </main>
  );
}

export default App;
