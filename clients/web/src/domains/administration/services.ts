import { apiFetch } from "@/lib/api/client"
import type { ApplicationAssignment, ApplicationRole, DirectoryUser, IdentityProviderInput, ManagedApplication, ManagedIdentityProvider } from "./types"

const json = (body: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })

export const listUsers = () => apiFetch<DirectoryUser[]>("/authentication/users/")
export const createUser = (email: string, is_staff: boolean, is_active: boolean) =>
  apiFetch<DirectoryUser>("/authentication/users/", json({ email, is_staff, is_active }))
export const deleteUser = (id: number) => apiFetch<void>(`/authentication/users/${id}/`, { method: "DELETE" })

export const listApplications = () => apiFetch<ManagedApplication[]>("/applications/")
export const createApplication = (body: Pick<ManagedApplication, "key" | "name" | "description" | "homepage_url">) =>
  apiFetch<ManagedApplication>("/applications/", json(body))
export const updateApplication = (id: number, body: Partial<Pick<ManagedApplication, "key" | "name" | "description" | "homepage_url">>) =>
  apiFetch<ManagedApplication>(`/applications/${id}/`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
export const deleteApplication = (id: number) => apiFetch<void>(`/applications/${id}/`, { method: "DELETE" })

export const listRoles = () => apiFetch<ApplicationRole[]>("/applications/roles/")
export const createRole = (application: number, key: string, name: string, description: string) =>
  apiFetch<ApplicationRole>("/applications/roles/", json({ application, key, name, description }))
export const deleteRole = (id: number) => apiFetch<void>(`/applications/roles/${id}/`, { method: "DELETE" })

export const listAssignments = () => apiFetch<ApplicationAssignment[]>("/applications/assignments/")
export const createAssignment = (application: number, user: number, role: number) =>
  apiFetch<ApplicationAssignment>("/applications/assignments/", json({ application, user, role }))
export const deleteAssignment = (id: number) => apiFetch<void>(`/applications/assignments/${id}/`, { method: "DELETE" })

export const listIdentityProviders = () => apiFetch<ManagedIdentityProvider[]>("/identity-providers/")
export const createIdentityProvider = (body: IdentityProviderInput) =>
  apiFetch<ManagedIdentityProvider>("/identity-providers/", json(body))
export const updateIdentityProvider = (id: number, body: Partial<IdentityProviderInput>) =>
  apiFetch<ManagedIdentityProvider>(`/identity-providers/${id}/`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  })
export const deleteIdentityProvider = (id: number) => apiFetch<void>(`/identity-providers/${id}/`, { method: "DELETE" })
export const testIdentityProvider = (id: number) =>
  apiFetch<{ status: "success" | "error"; detail: string }>(`/identity-providers/${id}/test/`, { method: "POST" })
