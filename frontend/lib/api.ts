import type { AEORequest, AEOResponse, FanoutRequest, FanoutResponse } from "./types";

const BASE = "/api";

// Human-friendly messages for known backend error codes
const ERROR_MESSAGES: Record<string, string> = {
  url_fetch_failed:  "Couldn't fetch that URL. Check it's publicly accessible and try again.",
  llm_unavailable:   "The AI model is temporarily unavailable. Please try again in a moment.",
  rate_limit_exceeded: "Too many requests. Please wait a minute before trying again.",
  unknown_error:     "Something went wrong. Please try again.",
};

export class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "APIError";
  }

  /** Returns a user-facing message, falling back to the raw message. */
  get friendly(): string {
    return ERROR_MESSAGES[this.code] ?? this.message;
  }
}

function isOfflineError(err: unknown): boolean {
  return err instanceof TypeError && err.message.toLowerCase().includes("fetch");
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
  try {
    const res = await fetch(`${BASE}/aeo/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<AEOResponse>(res);
  } catch (err) {
    if (isOfflineError(err)) {
      throw new APIError(0, "backend_offline", "Cannot reach the backend. Is it running on localhost:8000?");
    }
    throw err;
  }
}

export async function generateFanout(req: FanoutRequest): Promise<FanoutResponse> {
  try {
    const res = await fetch(`${BASE}/fanout/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<FanoutResponse>(res);
  } catch (err) {
    if (isOfflineError(err)) {
      throw new APIError(0, "backend_offline", "Cannot reach the backend. Is it running on localhost:8000?");
    }
    throw err;
  }
}

// Returns the raw Response for SSE streaming — caller handles the stream
export async function streamFanout(req: FanoutRequest): Promise<Response> {
  try {
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
  } catch (err) {
    if (isOfflineError(err)) {
      throw new APIError(0, "backend_offline", "Cannot reach the backend. Is it running on localhost:8000?");
    }
    throw err;
  }
}
