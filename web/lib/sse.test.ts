import { describe, expect, it } from "vitest"

import { parseSse } from "./sse"

describe("parseSse", () => {
  it("lê vários eventos de um chunk só", () => {
    const { events, rest } = parseSse(
      'data: {"type":"sources","sources":[],"sources_used":0}\n\ndata: {"type":"delta","text":"oi"}\n\n',
    )

    expect(events).toHaveLength(2)
    expect(events[1]).toEqual({ type: "delta", text: "oi" })
    expect(rest).toBe("")
  })

  it("segura o evento cortado ao meio em vez de perdê-lo", () => {
    // O caso que a rede produz sozinha: o chunk acaba no meio do JSON.
    const primeiro = parseSse('data: {"type":"delta","te')
    expect(primeiro.events).toEqual([])

    const segundo = parseSse(primeiro.rest + 'xt":"ola"}\n\n')
    expect(segundo.events).toEqual([{ type: "delta", text: "ola" }])
    expect(segundo.rest).toBe("")
  })

  it("preserva quebras de linha dentro do texto", () => {
    // Se o enquadramento fosse por linha, isto viraria dois eventos truncados.
    const { events } = parseSse(
      `data: ${JSON.stringify({ type: "delta", text: "linha 1\nlinha 2" })}\n\n`,
    )

    expect(events).toEqual([{ type: "delta", text: "linha 1\nlinha 2" }])
  })

  it("ignora evento malformado e continua lendo os seguintes", () => {
    const { events } = parseSse('data: {isso não é json}\n\ndata: {"type":"done"}\n\n')

    expect(events).toEqual([{ type: "done" }])
  })
})
