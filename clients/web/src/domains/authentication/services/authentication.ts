import {
  apiFetch,
  getApiUrl,
} from "@/lib/api/client"

import type {
  AuthUser,
  LoginCredentials,
  LoginResponse,
  RefreshResponse,
} from "@/domains/authentication/types/authentication"


export async function login(
  credentials: LoginCredentials,
  signal?: AbortSignal,
): Promise<LoginResponse> {
  return apiFetch<LoginResponse>(
    "/authentication/login/",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(
        credentials,
      ),
      signal,
    },
  )
}


export async function startGoogleLogin(
  providerKey: string,
): Promise<void> {
  const response = await apiFetch<{
    authorization_url: string
  }>(
    `/authentication/google/${encodeURIComponent(providerKey)}/start/`,
    {
      method: "GET",
      credentials: "include",
    },
  )

  window.location.assign(response.authorization_url)
}


export async function startMicrosoftLogin(
  providerKey: string,
): Promise<void> {
  const response = await apiFetch<{
    authorization_url: string
  }>(
    `/authentication/microsoft/${encodeURIComponent(providerKey)}/start/`,
    {
      method: "GET",
      credentials: "include",
    },
  )

  window.location.assign(response.authorization_url)
}


export async function startAppleLogin(providerKey: string): Promise<void> {
  const response = await apiFetch<{ authorization_url: string }>(
    `/authentication/apple/${encodeURIComponent(providerKey)}/start/`,
    { method: "GET", credentials: "include" },
  )
  window.location.assign(response.authorization_url)
}


export async function startGenericOIDCLogin(providerKey: string): Promise<void> {
  const response = await apiFetch<{ authorization_url: string }>(
    `/authentication/oidc/${encodeURIComponent(providerKey)}/start/`,
    { method: "GET", credentials: "include" },
  )
  window.location.assign(response.authorization_url)
}


export async function startCertificateLogin(
  providerKey: string,
): Promise<void> {
  const response = await apiFetch<{
    authentication_url: string
  }>(
    `/authentication/x509/${encodeURIComponent(providerKey)}/start/`,
    { method: "GET", credentials: "include" },
  )
  window.location.assign(response.authentication_url)
}


function decodeBase64url(value: string): ArrayBuffer {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - value.length % 4) % 4)
  const bytes = Uint8Array.from(atob(base64), (character) => character.charCodeAt(0))
  return bytes.buffer
}


function encodeBase64url(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value)
  let binary = ""
  bytes.forEach((byte) => { binary += String.fromCharCode(byte) })
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
}


export async function startPasskeyLogin(providerKey: string): Promise<LoginResponse> {
  if (!window.PublicKeyCredential) throw new Error("Aquest navegador no admet passkeys.")
  const start = await apiFetch<{ flow_token: string; public_key: PublicKeyCredentialRequestOptionsJSON }>(
    `/authentication/webauthn/${encodeURIComponent(providerKey)}/login/options/`,
    { method: "POST", credentials: "include" },
  )
  const options = start.public_key
  const publicKey = {
    ...options,
    challenge: decodeBase64url(options.challenge),
    allowCredentials: options.allowCredentials?.map((item) => ({
      ...item,
      id: decodeBase64url(item.id),
      type: "public-key" as const,
      transports: item.transports as AuthenticatorTransport[] | undefined,
    })),
  } as unknown as PublicKeyCredentialRequestOptions
  const result = await navigator.credentials.get({ publicKey }) as PublicKeyCredential | null
  if (!result) throw new Error("S'ha cancel·lat l'accés amb passkey.")
  const assertion = result.response as AuthenticatorAssertionResponse
  const credential = {
    id: result.id, rawId: encodeBase64url(result.rawId), type: result.type,
    response: {
      clientDataJSON: encodeBase64url(assertion.clientDataJSON),
      authenticatorData: encodeBase64url(assertion.authenticatorData),
      signature: encodeBase64url(assertion.signature),
      userHandle: assertion.userHandle ? encodeBase64url(assertion.userHandle) : null,
    },
    clientExtensionResults: result.getClientExtensionResults(),
  }
  return apiFetch<LoginResponse>(
    `/authentication/webauthn/${encodeURIComponent(providerKey)}/login/verify/`,
    { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ flow_token: start.flow_token, credential }) },
  )
}


export async function registerPasskey(providerKey: string, name = "Passkey"): Promise<{ id: number; name: string }> {
  if (!window.PublicKeyCredential) throw new Error("Aquest navegador no admet passkeys.")
  const start = await apiFetch<{ flow_token: string; public_key: PublicKeyCredentialCreationOptionsJSON }>(
    `/authentication/webauthn/${encodeURIComponent(providerKey)}/register/options/`,
    { method: "POST", credentials: "include" },
  )
  const options = start.public_key
  const publicKey = {
    ...options,
    challenge: decodeBase64url(options.challenge),
    user: { ...options.user, id: decodeBase64url(options.user.id) },
    excludeCredentials: options.excludeCredentials?.map((item) => ({ ...item, id: decodeBase64url(item.id), type: "public-key" as const, transports: item.transports as AuthenticatorTransport[] | undefined })),
  } as unknown as PublicKeyCredentialCreationOptions
  const result = await navigator.credentials.create({ publicKey }) as PublicKeyCredential | null
  if (!result) throw new Error("S'ha cancel·lat el registre de la passkey.")
  const attestation = result.response as AuthenticatorAttestationResponse
  const credential = {
    id: result.id, rawId: encodeBase64url(result.rawId), type: result.type,
    response: {
      clientDataJSON: encodeBase64url(attestation.clientDataJSON),
      attestationObject: encodeBase64url(attestation.attestationObject),
      transports: attestation.getTransports(),
    },
    clientExtensionResults: result.getClientExtensionResults(),
  }
  return apiFetch(`/authentication/webauthn/${encodeURIComponent(providerKey)}/register/verify/`, {
    method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ flow_token: start.flow_token, credential, name }),
  })
}


export async function completeExternalLogin(
  code: string,
): Promise<LoginResponse> {
  return apiFetch<LoginResponse>(
    "/authentication/external/complete/",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code }),
    },
  )
}


export async function refreshAccessToken(
  refreshToken: string,
  signal?: AbortSignal,
): Promise<RefreshResponse> {
  return apiFetch<RefreshResponse>(
    "/authentication/refresh/",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh:
          refreshToken,
      }),
      signal,
    },
  )
}


export async function getCurrentUser(
  accessToken: string,
  signal?: AbortSignal,
): Promise<AuthUser> {
  return apiFetch<AuthUser>(
    "/authentication/me/",
    {
      method: "GET",
      credentials: "include",
      headers: {
        Authorization:
          `Bearer ${accessToken}`,
      },
      signal,
    },
  )
}


export async function logout(
  refreshToken: string,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(
    getApiUrl(
      "/authentication/logout/",
    ),
    {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh:
          refreshToken,
      }),
      signal,
    },
  )

  if (
    !response.ok
  ) {
    throw new Error(
      `La petició ha fallat: `
      + `${response.status} `
      + response.statusText,
    )
  }
}
