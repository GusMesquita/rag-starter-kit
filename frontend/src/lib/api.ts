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
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, `/ask failed with ${response.status}`);
  }
  return (await response.json()) as AskResponse;
}
