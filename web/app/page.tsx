import { ChatPanel } from "@/components/chat/chat-panel"

export default function Page() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">rag-starter-kit</h1>
        <p className="text-muted-foreground text-sm">
          Pergunte aos documentos ingeridos. A resposta chega token a token e
          cada fonte vem com a distância que a trouxe.
        </p>
      </header>

      <ChatPanel />
    </main>
  )
}
