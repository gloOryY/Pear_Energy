import { api } from './config';
import { useAuth } from '../stores/auth';

let refreshing: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  const { refreshToken, setAuth, user, clear } = useAuth.getState();
  if (!refreshToken) return false;
  try {
    const r = await fetch(api('auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!r.ok) throw new Error();
    const d = await r.json();
    setAuth(d.access_token, d.refresh_token, user);
    return true;
  } catch {
    clear();
    return false;
  }
}

export async function refreshOnce(): Promise<boolean> {
  if (!refreshing) {
    refreshing = doRefresh().finally(() => { refreshing = null; });
  }
  return refreshing;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function request<T>(path: string, opts: RequestInit = {}, retry = true): Promise<T> {
  const { accessToken } = useAuth.getState();
  const headers: Record<string, string> = { ...(opts.headers as any) };
  if (!(opts.body instanceof FormData)) {
    headers['Content-Type'] ??= 'application/json';
  }
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }
  const r = await fetch(api(path), { ...opts, headers });
  if (r.status === 401 && retry) {
    if (await refreshOnce()) return request<T>(path, opts, false);
  }
  if (!r.ok) {
    let msg = `${r.status}`;
    try {
      const d = await r.json();
      msg = typeof d.detail === 'string' ? d.detail : JSON.stringify(d.detail ?? d);
    } catch {}
    throw new ApiError(r.status, msg);
  }
  if (r.status === 204) return undefined as T;
  const ct = r.headers.get('content-type') ?? '';
  return ct.includes('application/json') ? r.json() : (r.text() as T);
}

export const get = <T>(path: string) => request<T>(path);
export const post = <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined });
export const patch = <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
export const del = <T>(path: string) => request<T>(path, { method: 'DELETE' });
