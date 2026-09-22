import "server-only"

// `server-only` não é decoração: importar este módulo de um Client Component
// vira erro de build. É a versão verificável de "a chave nunca chega ao
// browser" — nenhuma variável aqui leva o prefixo NEXT_PUBLIC_, que é o que
// inlina valores no bundle.

const BASE_URL = process.env.RAG_API_URL ?? "http://localhost:8000"

/** Teto espelhado do `max_length` do backend: recusar aqui evita uma ida à API. */
export const MAX_QUESTION_LENGTH = 2_000

export function askStream(question: string, signal: AbortSignal): Promise<Response> {
  const key = process.env.RAG_API_KEY
  return fetch(`${BASE_URL}/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(key ? { "X-API-Key": key } : {}),
    },
    body: JSON.stringify({ question }),
    // Se o leitor fecha a aba, não há motivo para o backend seguir gastando
    // tokens da Anthropic numa resposta que ninguém vai ler.
    signal,
  })
}
