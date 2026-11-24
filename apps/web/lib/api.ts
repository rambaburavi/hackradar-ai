const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export interface HealthResponse {
  status: string;
}

export const api = {
  async health(): Promise<HealthResponse> {
    const response = await fetch(`${API_URL}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) {
      throw new Error("Backend health check failed");
    }

    return response.json();
  },
};