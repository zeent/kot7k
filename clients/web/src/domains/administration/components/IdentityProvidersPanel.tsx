"use client"

import { useEffect, useMemo, useState, type FormEvent } from "react"
import { Button, DataTable, InlineNotification, Modal, PasswordInput, Select, SelectItem, Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow, TableToolbar, TableToolbarContent, TableToolbarSearch, TextInput, Toggle } from "@carbon/react"
import { Add, Edit, Renew, TrashCan } from "@carbon/icons-react"

import { useAdministrationMessages } from "../i18n"
import { createIdentityProvider, deleteIdentityProvider, listIdentityProviders, testIdentityProvider, updateIdentityProvider } from "../services"
import type { IdentityProviderInput, IdentityProviderType, ManagedIdentityProvider } from "../types"

const PROVIDER_TYPES: { value: IdentityProviderType; label: string }[] = [
  { value: "local", label: "Email / password" }, { value: "ldap", label: "LDAP / Active Directory" },
  { value: "oidc", label: "OpenID Connect" }, { value: "google", label: "Google" },
  { value: "microsoft", label: "Microsoft Entra ID" }, { value: "apple", label: "Apple" },
  { value: "x509", label: "X.509 / FNMT" }, { value: "webauthn", label: "Passkey / WebAuthn" },
]

const FIELD_NAMES: Record<IdentityProviderType, string[]> = {
  local: [], google: ["client_id", "allowed_domains"],
  microsoft: ["client_id", "tenant_id", "allowed_domains", "allowed_tenant_ids"],
  apple: ["client_id", "team_id", "key_id", "allowed_domains"],
  oidc: ["issuer", "client_id", "scopes", "allowed_domains"],
  x509: ["email_header", "verification_header"], webauthn: ["rp_id", "origin"],
  ldap: ["server_uri", "port", "base_dn", "bind_dn", "user_filter", "email_attribute", "first_name_attribute", "last_name_attribute"],
}

const LIST_FIELDS = new Set(["allowed_domains", "allowed_tenant_ids", "scopes"])

export default function IdentityProvidersPanel() {
  const t = useAdministrationMessages()
  const [providers, setProviders] = useState<ManagedIdentityProvider[]>([])
  const [editing, setEditing] = useState<ManagedIdentityProvider | "new" | null>(null)
  const [search, setSearch] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [providerType, setProviderType] = useState<IdentityProviderType>("local")
  const [key, setKey] = useState("")
  const [name, setName] = useState("")
  const [enabled, setEnabled] = useState(false)
  const [secret, setSecret] = useState("")
  const [configuration, setConfiguration] = useState<Record<string, string>>({})

  async function load() {
    try { setProviders(await listIdentityProviders()); setError(null) }
    catch (caught) { setError(caught instanceof Error ? caught.message : t.error) }
  }
  useEffect(() => {
    const timeout = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function open(provider: ManagedIdentityProvider | "new") {
    setEditing(provider); setSecret(""); setError(null); setNotice(null)
    if (provider === "new") {
      setProviderType("local"); setKey(""); setName(""); setEnabled(false); setConfiguration({})
    } else {
      setProviderType(provider.provider_type); setKey(provider.key); setName(provider.name); setEnabled(provider.is_enabled)
      setConfiguration(Object.fromEntries(Object.entries(provider.configuration).map(([field, value]) => [field, Array.isArray(value) ? value.join(", ") : String(value ?? "")])))
    }
  }

  const fields = FIELD_NAMES[providerType]
  const filtered = useMemo(() => {
    const needle = search.trim().toLocaleLowerCase()
    return needle ? providers.filter((provider) => `${provider.name} ${provider.key} ${provider.provider_type}`.toLocaleLowerCase().includes(needle)) : providers
  }, [providers, search])

  function fieldLabel(field: string): string {
    const labels: Record<string, string> = {
      client_id: t.clientId, tenant_id: t.tenantId, issuer: t.issuer, allowed_domains: t.allowedDomains,
      allowed_tenant_ids: t.allowedTenantIds, team_id: t.teamId, key_id: t.keyId, rp_id: t.rpId,
      origin: t.origin, email_header: t.emailHeader, verification_header: t.verificationHeader,
      server_uri: t.serverUri, port: t.port, base_dn: t.baseDn, bind_dn: t.bindDn,
      user_filter: t.userFilter, email_attribute: t.emailAttribute,
      first_name_attribute: t.firstNameAttribute, last_name_attribute: t.lastNameAttribute, scopes: t.scopes,
    }
    return labels[field] ?? field
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); if (!editing) return
    setSaving(true); setError(null)
    const normalizedConfig = Object.fromEntries(fields.filter((field) => configuration[field]?.trim()).map((field) => [field, LIST_FIELDS.has(field) ? configuration[field].split(",").map((value) => value.trim()).filter(Boolean) : field === "port" ? Number(configuration[field]) : configuration[field].trim()]))
    const body: IdentityProviderInput = { key, name, provider_type: providerType, is_enabled: enabled, display_order: editing === "new" ? providers.length : editing.display_order, configuration: normalizedConfig }
    if (secret) body.secret = secret
    try {
      if (editing === "new") await createIdentityProvider(body); else await updateIdentityProvider(editing.id, body)
      setEditing(null); await load()
    } catch (caught) { setError(caught instanceof Error ? caught.message : t.error) }
    finally { setSaving(false) }
  }

  async function remove(provider: ManagedIdentityProvider) {
    if (!window.confirm(t.confirmDelete)) return
    try { await deleteIdentityProvider(provider.id); await load() }
    catch (caught) { setError(caught instanceof Error ? caught.message : t.error) }
  }

  async function test(provider: ManagedIdentityProvider) {
    setNotice(null); setError(null)
    try { const result = await testIdentityProvider(provider.id); setNotice(result.detail); await load() }
    catch (caught) { setError(caught instanceof Error ? caught.message : t.testError); await load() }
  }

  const headers = [{ key: "name", header: t.name }, { key: "type", header: t.providerType }, { key: "status", header: t.status }, { key: "test", header: t.test }, { key: "actions", header: t.actions }]
  const rows = filtered.map((provider) => ({ id: String(provider.id), name: provider.name, type: PROVIDER_TYPES.find((item) => item.value === provider.provider_type)?.label ?? provider.provider_type, status: provider.is_enabled ? t.enabled : t.disabled, test: provider.last_test_status === "success" ? t.testSuccess : provider.last_test_status === "error" ? t.testError : t.testNever, actions: provider }))

  return <>
    {error && <InlineNotification kind="error" lowContrast title={t.error} subtitle={error} onClose={() => setError(null)} />}
    {notice && <InlineNotification kind="success" lowContrast title={t.testSuccess} subtitle={notice} onClose={() => setNotice(null)} />}
    <DataTable rows={rows} headers={headers}>{({ rows: carbonRows, headers: carbonHeaders, getHeaderProps, getRowProps, getTableProps }) => <TableContainer aria-label={t.identityProviders}>
      <TableToolbar><TableToolbarContent><TableToolbarSearch persistent placeholder={`${t.search}: ${t.identityProviders}`} value={search} onChange={(_event, value) => setSearch(value ?? "")} /><Button renderIcon={Add} onClick={() => open("new")}>{t.addIdentityProvider}</Button></TableToolbarContent></TableToolbar>
      <Table {...getTableProps()}><TableHead><TableRow>{carbonHeaders.map((header) => { const props = getHeaderProps({ header }); return <TableHeader {...props} key={props.key}>{header.header}</TableHeader> })}</TableRow></TableHead>
        <TableBody>{carbonRows.length ? carbonRows.map((row) => { const props = getRowProps({ row }); const provider = row.cells.at(-1)?.value as ManagedIdentityProvider; return <TableRow {...props} key={props.key}>{row.cells.slice(0, -1).map((cell) => <TableCell key={cell.id}>{cell.value}</TableCell>)}<TableCell><Button hasIconOnly kind="ghost" size="sm" renderIcon={Renew} iconDescription={t.test} onClick={() => void test(provider)} /><Button hasIconOnly kind="ghost" size="sm" renderIcon={Edit} iconDescription={t.edit} onClick={() => open(provider)} /><Button hasIconOnly kind="danger--ghost" size="sm" renderIcon={TrashCan} iconDescription={t.delete} onClick={() => void remove(provider)} /></TableCell></TableRow> }) : <TableRow><TableCell colSpan={headers.length}>{t.empty}</TableCell></TableRow>}</TableBody>
      </Table>
    </TableContainer>}</DataTable>

    <Modal open={editing !== null} modalHeading={editing === "new" ? t.addIdentityProvider : t.edit} primaryButtonText={editing === "new" ? t.create : t.update} secondaryButtonText={t.cancel} primaryButtonDisabled={saving} onRequestClose={() => setEditing(null)} onRequestSubmit={() => (document.getElementById("identity-provider-form") as HTMLFormElement | null)?.requestSubmit()}>
      <form id="identity-provider-form" className="administration-console__form" onSubmit={(event) => void submit(event)}>
        <TextInput id="provider-name" required labelText={t.name} value={name} onChange={(event) => setName(event.target.value)} />
        <TextInput id="provider-key" required disabled={editing !== "new"} labelText={t.key} value={key} onChange={(event) => setKey(event.target.value.toLowerCase())} />
        <Select id="provider-type" labelText={t.providerType} value={providerType} onChange={(event) => { setProviderType(event.target.value as IdentityProviderType); setConfiguration({}) }}>{PROVIDER_TYPES.map((type) => <SelectItem key={type.value} value={type.value} text={type.label} />)}</Select>
        <Toggle id="provider-enabled" labelText={t.status} labelA={t.disabled} labelB={t.enabled} toggled={enabled} onToggle={setEnabled} />
        {fields.map((field) => <TextInput key={field} id={`provider-${field}`} required={["client_id", "tenant_id", "issuer", "server_uri", "base_dn", "user_filter", "email_attribute", "rp_id", "origin", "email_header", "team_id", "key_id"].includes(field)} type={["issuer", "server_uri", "origin"].includes(field) ? "url" : field === "port" ? "number" : "text"} labelText={fieldLabel(field)} value={configuration[field] ?? ""} onChange={(event) => setConfiguration((current) => ({ ...current, [field]: event.target.value }))} />)}
        {!["local", "webauthn", "x509"].includes(providerType) && <PasswordInput id="provider-secret" labelText={t.secret} helperText={editing !== "new" ? t.secretHint : undefined} value={secret} onChange={(event) => setSecret(event.target.value)} />}
      </form>
    </Modal>
  </>
}
