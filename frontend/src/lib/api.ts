export interface AskResponse {
  answer: string;
  sources_used: number;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Sem API key aqui, de propósito: tudo em `import.meta.env.VITE_*` é inlinado
// no bundle pelo Vite e fica legível para qualquer visitante. A chave vive no
// backend; este SPA fala com uma origem já liberada no CORS (ou, em produção,
// com um proxy/BFF que injeta o X-API-Key server-side).

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, `/ask failed with ${response.status}`);
  }
  return (await response.json()) as AskResponse;
}
