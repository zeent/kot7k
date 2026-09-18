export type DirectoryUser = {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_active: boolean
  is_staff: boolean
  date_joined: string
  created_at: string
  updated_at: string
}

export type ManagedApplication = {
  id: number
  key: string
  name: string
  description: string
  homepage_url: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ApplicationRole = {
  id: number
  application: number
  application_name: string
  key: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export type ApplicationAssignment = {
  id: number
  application: number
  application_name: string
  user: number
  user_email: string
  role: number
  role_name: string
  created_at: string
  updated_at: string
}

export type IdentityProviderType = "local" | "google" | "microsoft" | "apple" | "x509" | "webauthn" | "oidc" | "ldap"

export type ManagedIdentityProvider = {
  id: number
  key: string
  provider_type: IdentityProviderType
  name: string
  is_enabled: boolean
  display_order: number
  configuration: Record<string, unknown>
  has_secret_reference: boolean
  last_tested_at: string | null
  last_test_status: "never" | "success" | "error"
  last_test_error: string
  created_at: string
  updated_at: string
}

export type IdentityProviderInput = Pick<ManagedIdentityProvider, "key" | "provider_type" | "name" | "is_enabled" | "display_order" | "configuration"> & {
  secret?: string
}
