"use client"

import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"
import { Input } from "@/components/ui/input"
import { rotuloDeFontes } from "@/lib/fontes"
import { parseSse, type Citation } from "@/lib/sse"

interface Turno {
  question: string
  answer: string
  citations: Citation[]
  status: "streaming" | "done" | "error"
  error?: string
}

export function ChatPanel() {
  const [turnos, setTurnos] = useState<Turno[]>([])
  const [pergunta, setPergunta] = useState("")
  const ocupado = turnos.at(-1)?.status === "streaming"

  // Sempre o último turno: é o único que está sendo escrito.
  function atualizarUltimo(patch: (turno: Turno) => Partial<Turno>) {
    setTurnos((anteriores) =>
      anteriores.map((turno, indice) =>
        indice === anteriores.length - 1 ? { ...turno, ...patch(turno) } : turno,
      ),
    )
  }

  async function perguntar(evento: React.FormEvent) {
    evento.preventDefault()
    const question = pergunta.trim()
    if (!question || ocupado) return

    setPergunta("")
    setTurnos((anteriores) => [
      ...anteriores,
      { question, answer: "", citations: [], status: "streaming" },
    ])

    try {
      const resposta = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      })

      if (!resposta.ok || !resposta.body) {
        const corpo = await resposta.json().catch(() => null)
        atualizarUltimo(() => ({
          status: "error",
          error: corpo?.error ?? `a API respondeu ${resposta.status}`,
        }))
        return
      }

      const leitor = resposta.body.pipeThrough(new TextDecoderStream()).getReader()
      // O buffer atravessa as iterações porque um evento pode chegar partido
      // entre dois chunks; `parseSse` devolve o pedaço incompleto de volta.
      let buffer = ""

      for (;;) {
        const { done, value } = await leitor.read()
        if (done) break

        buffer += value
        const { events, rest } = parseSse(buffer)
        buffer = rest

        for (const evento of events) {
          if (evento.type === "sources") {
            atualizarUltimo(() => ({ citations: evento.sources }))
          } else if (evento.type === "delta") {
            atualizarUltimo((turno) => ({ answer: turno.answer + evento.text }))
          } else if (evento.type === "error") {
            atualizarUltimo(() => ({ status: "error", error: evento.error }))
          } else if (evento.type === "done") {
            atualizarUltimo(() => ({ status: "done" }))
          }
        }
      }
    } catch {
      atualizarUltimo(() => ({ status: "error", error: "a conexão caiu" }))
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Região de status em vez de `aria-live` no texto da resposta: um live
          region que recebe token a token faz o leitor de tela recomeçar a
          falar a cada palavra. Aqui ele anuncia as transições, que é a
          informação que um leitor cego não obtém olhando o cursor piscar. */}
      <p className="sr-only" role="status" aria-live="polite">
        {ocupado
          ? "Respondendo"
          : turnos.at(-1)?.status === "done"
            ? `Resposta pronta, ${rotuloDeFontes(turnos.at(-1)?.citations.length ?? 0)}`
            : ""}
      </p>

      {turnos.map((turno, indice) => (
        <Card key={indice}>
          <CardHeader>
            <CardTitle className="text-base font-medium">{turno.question}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p
              className="text-sm whitespace-pre-wrap"
              // Marca "ainda escrevendo" para tecnologia assistiva sem
              // transformar o parágrafo inteiro num live region.
              aria-busy={turno.status === "streaming"}
            >
              {turno.answer}
              {turno.status === "streaming" && (
                <span className="bg-foreground ml-0.5 inline-block h-4 w-2 animate-pulse align-text-bottom" />
              )}
            </p>

            {turno.status === "error" && (
              <p className="text-destructive text-sm">Falhou: {turno.error}</p>
            )}

            <Citacoes citations={turno.citations} status={turno.status} />
          </CardContent>
        </Card>
      ))}

      <form onSubmit={perguntar} className="flex gap-2">
        <Input
          value={pergunta}
          onChange={(evento) => setPergunta(evento.target.value)}
          placeholder="Pergunte algo sobre os documentos ingeridos"
          aria-label="Pergunta"
          disabled={ocupado}
        />
        <Button type="submit" disabled={ocupado || pergunta.trim() === ""}>
          {ocupado ? "Respondendo…" : "Perguntar"}
        </Button>
      </form>
    </div>
  )
}

function Citacoes({ citations, status }: { citations: Citation[]; status: Turno["status"] }) {
  // Nenhuma fonte com a resposta pronta não é ausência de informação: é a
  // informação de que o modelo não tinha em que se apoiar.
  if (citations.length === 0) {
    return status === "done" ? (
      <p className="text-muted-foreground text-xs">Nenhum documento relevante.</p>
    ) : null
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-muted-foreground text-xs">Fontes:</span>
      {citations.map((citation) => (
        <HoverCard key={citation.source}>
          {/* Um <button> e não uma <span>: a dica também tem que abrir pelo
              teclado, senão a distância só existe para quem usa mouse. */}
          <HoverCardTrigger
            render={
              <button type="button" className="cursor-help">
                <Badge variant="secondary">{citation.source}</Badge>
              </button>
            }
          />
          <HoverCardContent className="w-auto">
            <p className="font-medium">{citation.source}</p>
            <p className="text-muted-foreground mt-1 text-xs">
              Distância cosseno {citation.distance} — quanto menor, mais próximo o
              trecho ficou da pergunta. O corte está em <code>MAX_DISTANCE</code>.
            </p>
          </HoverCardContent>
        </HoverCard>
      ))}
    </div>
  )
}
