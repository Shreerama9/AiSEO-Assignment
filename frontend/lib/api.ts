import type { AEORequest, AEOResponse, FanoutRequest, FanoutResponse } from "./types";

const BASE = "/api";

class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let code = "unknown_error";
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      code = body?.detail?.error ?? body?.error ?? code;
      message = body?.detail?.message ?? body?.message ?? message;
    } catch {
      // ignore parse errors
    }
    throw new APIError(res.status, code, message);
  }
  return res.json() as Promise<T>;
}

export async function analyzeAEO(req: AEORequest): Promise<AEOResponse> {
  const res = await fetch(`${BASE}/aeo/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse<AEOResponse>(res);
}

export async function generateFanout(req: FanoutRequest): Promise<FanoutResponse> {
  const res = await fetch(`${BASE}/fanout/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse<FanoutResponse>(res);
}

// Returns the raw Response for SSE streaming — caller handles the stream
export async function streamFanout(req: FanoutRequest): Promise<Response> {
  const res = await fetch(`${BASE}/fanout/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const code = body?.detail?.error ?? "stream_error";
    const msg = body?.detail?.message ?? `HTTP ${res.status}`;
    throw new APIError(res.status, code, msg);
  }
  return res;
}

export { APIError };
