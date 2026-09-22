/**
 * Rótulo do número de fontes, já com a pluralização resolvida.
 *
 * Existe porque quem lê este texto costuma ser um leitor de tela, e "1 fontes"
 * é dito em voz alta. Zero também não é "0 fontes": é a informação de que o
 * modelo respondeu sem ter em que se apoiar.
 */
export function rotuloDeFontes(quantidade: number): string {
  if (quantidade === 0) return "sem fontes no contexto"
  if (quantidade === 1) return "1 fonte usada"
  return `${quantidade} fontes usadas`
}
