// Minimal client-side auth: stores the JWT in localStorage and exposes helpers.
// Note (hardening, future phase): an httpOnly cookie is safer against XSS.

import { API_BASE } from "./api";

const TOKEN_KEY = "privrag_token";
const EMAIL_KEY = "privrag_email";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getEmail(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(EMAIL_KEY);
}

export function setSession(token: string, email: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(EMAIL_KEY, email);
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(EMAIL_KEY);
}

export interface AuthResult {
  access_token: string;
  token_type: string;
  email: string;
}

async function authRequest(path: string, email: string, password: string): Promise<AuthResult> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    let detail = "Error";
    try {
      detail = (await res.json())?.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : "Error");
  }
  return res.json();
}

export async function register(email: string, password: string): Promise<AuthResult> {
  const r = await authRequest("/auth/register", email, password);
  setSession(r.access_token, r.email);
  return r;
}

export async function login(email: string, password: string): Promise<AuthResult> {
  const r = await authRequest("/auth/login", email, password);
  setSession(r.access_token, r.email);
  return r;
}

export function logout(): void {
  clearSession();
}
