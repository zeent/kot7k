export type IdentityProviderType = "local" | "google" | "microsoft" | "apple" | "x509" | "webauthn" | "oidc" | "ldap"

export type PublicIdentityProvider = {
  key: string
  provider_type: IdentityProviderType
  name: string
}

export async function discoverIdentityProviders(): Promise<PublicIdentityProvider[]> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:10001"
  const response = await fetch(new URL("/api/identity-providers/discovery/", baseUrl), {
    cache: "no-store",
  })
  if (!response.ok) {
    throw new Error(`Identity-provider discovery failed with status ${response.status}.`)
  }
  return response.json() as Promise<PublicIdentityProvider[]>
}
