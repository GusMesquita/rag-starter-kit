import { MAX_QUESTION_LENGTH, askStream } from "@/lib/rag-api"

// Ao contrário do dashboard do lead-router, aqui o Route Handler tem função:
// a resposta precisa escorrer até o browser, e um Server Component só sabe
// entregar HTML pronto. Ele é o único lugar onde a chave aparece.
export const dynamic = "force-dynamic"

export async function POST(request: Request) {
  let corpo: unknown
  try {
    corpo = await request.json()
  } catch {
    return Response.json({ error: "corpo não é JSON" }, { status: 400 })
  }

  // Fronteira de confiança: o que chega do browser é validado aqui, não
  // repassado como veio. Sem isto, qualquer campo extra seguiria para a API.
  const question = (corpo as { question?: unknown })?.question
  if (typeof question !== "string" || question.trim() === "") {
    return Response.json({ error: "pergunta vazia" }, { status: 400 })
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    return Response.json({ error: "pergunta longa demais" }, { status: 413 })
  }

  let upstream: Response
  try {
    upstream = await askStream(question, request.signal)
  } catch {
    // Conexão recusada é o caso comum em dev; 502 é o que descreve "eu estou
    // de pé, quem está atrás de mim não está".
    return Response.json({ error: "a API de RAG não respondeu" }, { status: 502 })
  }

  if (!upstream.ok || !upstream.body) {
    // O status vem de lá (401, 429), mas não o corpo: a mensagem do backend
    // pode carregar detalhe interno que não interessa ao browser.
    return Response.json({ error: `a API respondeu ${upstream.status}` }, { status: upstream.status })
  }

  // Repasse do corpo sem bufferizar: reempacotar em texto aqui seguraria a
  // resposta inteira e desfaria o streaming que o backend acabou de produzir.
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  })
}
