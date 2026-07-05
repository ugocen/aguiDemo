export interface Identity {
  userId: string;
  email: string;
}

const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE ?? "dev";

/**
 * Bearer provider. In dev mode a stub token is returned so the app runs before
 * sign-in is wired. In entra mode this is where an MSAL acquired token is
 * returned; the MSAL wiring is added in Phase 2 / M-auth and only this module
 * and providers.tsx change.
 */
export async function getBearerToken(): Promise<string> {
  if (AUTH_MODE === "entra") {
    const token = await acquireEntraToken();
    if (token) return token;
  }
  return "dev-token";
}

export function currentIdentity(): Identity {
  return { userId: "dev-user", email: "dev@example.com" };
}

async function acquireEntraToken(): Promise<string | null> {
  return null;
}
