import { expect, it } from "vitest"

import { rotuloDeFontes } from "./fontes"

it("não diz '1 fontes' em voz alta", () => {
  expect(rotuloDeFontes(1)).toBe("1 fonte usada")
})

it("distingue nenhuma fonte de uma contagem", () => {
  expect(rotuloDeFontes(0)).toBe("sem fontes no contexto")
  expect(rotuloDeFontes(3)).toBe("3 fontes usadas")
})
