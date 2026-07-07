import {
  AccountInfo,
  InteractionRequiredAuthError,
  PublicClientApplication,
} from "@azure/msal-browser";

export interface Identity {
  userId: string;
  email: string;
}

const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE ?? "dev";
const CLIENT_ID = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID ?? "";
const TENANT_ID = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID ?? "";
// openid + profile are enough to receive an ID token; the backend validates it
// (audience = the app's client id). No custom API scope needs to be exposed.
const LOGIN_SCOPES = ["openid", "profile"];

let msal: PublicClientApplication | null = null;
let initPromise: Promise<void> | null = null;

function getMsal(): PublicClientApplication | null {
  if (typeof window === "undefined" || !CLIENT_ID || !TENANT_ID) return null;
  if (!msal) {
    msal = new PublicClientApplication({
      auth: {
        clientId: CLIENT_ID,
        authority: `https://login.microsoftonline.com/${TENANT_ID}`,
        redirectUri: process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI || window.location.origin,
      },
      cache: { cacheLocation: "localStorage" },
    });
  }
  return msal;
}

async function ready(pca: PublicClientApplication): Promise<void> {
  if (!initPromise) initPromise = pca.initialize();
  await initPromise;
  await pca.handleRedirectPromise().catch(() => null);
}

function activeAccount(pca: PublicClientApplication): AccountInfo | null {
  return pca.getActiveAccount() ?? pca.getAllAccounts()[0] ?? null;
}

/**
 * Bearer provider. In dev mode a stub token is returned so the app runs before
 * sign-in is wired. In entra mode this signs the user in with MSAL (PKCE, popup)
 * and returns the ID token, which the backend validates (issuer = the tenant,
 * audience = the app's client id). Only this module changes to swap auth.
 */
export async function getBearerToken(): Promise<string> {
  if (AUTH_MODE === "entra") {
    const token = await acquireEntraToken();
    if (token) return token;
  }
  return "dev-token";
}

export function currentIdentity(): Identity {
  const pca = msal;
  const account = pca ? activeAccount(pca) : null;
  if (account) {
    return { userId: account.localAccountId, email: account.username };
  }
  return { userId: "dev-user", email: "dev@example.com" };
}

async function acquireEntraToken(): Promise<string | null> {
  const pca = getMsal();
  if (!pca) return null;
  await ready(pca);

  let account = activeAccount(pca);
  if (!account) {
    try {
      const result = await pca.loginPopup({ scopes: LOGIN_SCOPES });
      pca.setActiveAccount(result.account);
      return result.idToken || null;
    } catch {
      return null;
    }
  }

  pca.setActiveAccount(account);
  try {
    const result = await pca.acquireTokenSilent({ scopes: LOGIN_SCOPES, account });
    return result.idToken || null;
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      try {
        const result = await pca.loginPopup({ scopes: LOGIN_SCOPES });
        pca.setActiveAccount(result.account);
        return result.idToken || null;
      } catch {
        return null;
      }
    }
    return null;
  }
}
