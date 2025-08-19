// Default to Next.js rewrite route to avoid cross-origin cookies in dev
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api';

export async function apiFetch(
  path,
  { method = 'GET', body, headers = {}, credentials = 'include', authRedirect = true } = {}
) {
  const opts = { method, headers: { ...headers }, credentials };
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body) {
    opts.body = body;
  }
  const res = await fetch(`${API_BASE}${path}`, opts);
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    if (res.status === 401 && authRedirect && typeof window !== 'undefined') {
      // Redirect to login page on unauthorized
      window.location.href = '/login';
      return; // prevent further handling
    }
    throw new Error(data && data.detail ? data.detail : text || `HTTP ${res.status}`);
  }
  return data;
}

export async function postJSON(path, payload, opts={}) {
  return apiFetch(path, { method: 'POST', body: payload, ...opts });
}
