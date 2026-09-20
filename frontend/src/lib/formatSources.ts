export function formatSourcesLabel(sourcesUsed: number): string {
  if (sourcesUsed === 0) return "sem fontes no contexto";
  if (sourcesUsed === 1) return "1 fonte usada";
  return `${sourcesUsed} fontes usadas`;
}
