export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  // In production, this reads from Authentik session cookie
  // For development, check localStorage
  return localStorage.getItem("auth_token");
}

export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}
