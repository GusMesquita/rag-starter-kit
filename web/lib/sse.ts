export interface Citation {
  source: string
  distance: number
}

export type StreamEvent =
  | { type: "sources"; sources: Citation[]; sources_used: number }
  | { type: "delta"; text: string }
  | { type: "done" }
  | { type: "error"; error: string }

/**
 * Consome os eventos completos de `buffer` e devolve o que sobrou.
 *
 * O resto importa: `fetch` entrega os bytes como a rede os entregou, não como
 * o protocolo os agrupou. Um evento pode chegar partido ao meio entre dois
 * chunks, e quem parseia chunk a chunk perde silenciosamente esse evento — o
 * sintoma é uma palavra faltando no meio da resposta, difícil de notar e
 * impossível de reproduzir de propósito.
 */
export function parseSse(buffer: string): { events: StreamEvent[]; rest: string } {
  const partes = buffer.split("\n\n")
  // O último pedaço só está completo se o buffer terminava no separador; caso
  // contrário ele é o começo do próximo evento e volta para o buffer.
  const rest = partes.pop() ?? ""
  const events: StreamEvent[] = []

  for (const parte of partes) {
    const linha = parte.split("\n").find((l) => l.startsWith("data:"))
    if (!linha) continue
    try {
      events.push(JSON.parse(linha.slice("data:".length)) as StreamEvent)
    } catch {
      // Evento malformado é ruído de transporte, não motivo para derrubar a
      // leitura do resto da resposta.
    }
  }

  return { events, rest }
}
