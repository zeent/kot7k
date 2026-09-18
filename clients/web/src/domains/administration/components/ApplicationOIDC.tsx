"use client"

import { useEffect, useState } from "react"
import { Button, Checkbox, InlineLoading, InlineNotification, Modal, Select, SelectItem, TextArea, TextInput, Toggle } from "@carbon/react"
import { useLocale } from "@/i18n/LocaleProvider"
import { apiFetch } from "@/lib/api/client"
import type { ManagedApplication } from "../types"

const messages = {
  ca: { title: "Autenticació OpenID Connect", intro: "Configura el client per connectar aquesta aplicació amb Kot7k. Authorization Code amb PKCE S256.", save: "Desa", close: "Tanca", loading: "Carregant…", error: "No s’ha pogut completar l’operació", saved: "Configuració desada", type: "Tipus de client", confidential: "Confidencial (servidor)", public: "Públic (sense secret)", redirects: "URLs de retorn autoritzades", lines: "Una URL per línia. HTTPS o HTTP a localhost.", scopes: "Scopes permesos", active: "Client habilitat", yes: "Sí", no: "No", secret: "Secret del client", secretHint: "Copia aquest secret ara: no es tornarà a mostrar. Introdueix-lo a l’aplicació que es connectarà a Kot7k.", rotate: "Renova el secret", confirm: "Renovar el secret invalidarà l’anterior immediatament. Vols continuar?", generated: "Es generarà en desar", unsaved: "Desa els canvis abans de renovar el secret.", leave: "Has copiat el secret? En tancar no es tornarà a mostrar." },
  es: { title: "Autenticación OpenID Connect", intro: "Configura el cliente para conectar esta aplicación con Kot7k. Authorization Code con PKCE S256.", save: "Guardar", close: "Cerrar", loading: "Cargando…", error: "No se ha podido completar la operación", saved: "Configuración guardada", type: "Tipo de cliente", confidential: "Confidencial (servidor)", public: "Público (sin secreto)", redirects: "URLs de retorno autorizadas", lines: "Una URL por línea. HTTPS o HTTP en localhost.", scopes: "Scopes permitidos", active: "Cliente habilitado", yes: "Sí", no: "No", secret: "Secreto del cliente", secretHint: "Copia este secreto ahora: no volverá a mostrarse. Introdúcelo en la aplicación que se conectará a Kot7k.", rotate: "Renovar secreto", confirm: "Renovar el secreto invalidará el anterior inmediatamente. ¿Quieres continuar?", generated: "Se generará al guardar", unsaved: "Guarda los cambios antes de renovar el secreto.", leave: "¿Has copiado el secreto? Al cerrar no volverá a mostrarse." },
  en: { title: "OpenID Connect authentication", intro: "Configure the client to connect this application to Kot7k. Authorization Code with PKCE S256.", save: "Save", close: "Close", loading: "Loading…", error: "The operation could not be completed", saved: "Configuration saved", type: "Client type", confidential: "Confidential (server)", public: "Public (no secret)", redirects: "Allowed callback URLs", lines: "One URL per line. HTTPS, or HTTP on localhost.", scopes: "Allowed scopes", active: "Client enabled", yes: "Yes", no: "No", secret: "Client secret", secretHint: "Copy this secret now: it will not be shown again. Enter it in the application connecting to Kot7k.", rotate: "Rotate secret", confirm: "Rotating the secret immediately invalidates the previous one. Continue?", generated: "Generated when saved", unsaved: "Save changes before rotating the secret.", leave: "Have you copied the secret? It will not be shown again after closing." },
}

type Client = { client_id: string; is_confidential: boolean; redirect_uris: string[]; allowed_scopes: string[]; is_active: boolean; client_secret?: string }
const scopes = ["openid", "email", "profile", "roles", "offline_access"]

export default function ApplicationOIDC({ application, onClose }: { application: ManagedApplication; onClose: () => void }) {
  const { locale } = useLocale()
  const t = messages[locale]
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [clientId, setClientId] = useState("")
  const [confidential, setConfidential] = useState(true)
  const [redirects, setRedirects] = useState("")
  const [selected, setSelected] = useState(["openid", "email", "profile"])
  const [active, setActive] = useState(true)
  const [secret, setSecret] = useState("")
  const [dirty, setDirty] = useState(false)
  const [saved, setSaved] = useState(false)
  const url = `/applications/${application.id}/oidc/`

  useEffect(() => {
    let cancelled = false
    apiFetch<Client | null>(url).then((data) => {
      if (cancelled) return
      if (data) {
        setClientId(data.client_id); setConfidential(data.is_confidential); setRedirects(data.redirect_uris.join("\n")); setSelected(data.allowed_scopes); setActive(data.is_active)
      }
      setLoading(false)
    }).catch((cause) => { if (!cancelled) { setError(String(cause)); setLoadFailed(true); setLoading(false) } })
    return () => { cancelled = true }
  }, [url])

  function close() { if (!busy && (!secret || window.confirm(t.leave))) onClose() }
  function change() { setDirty(true); setSaved(false) }
  async function save() {
    if (loading || busy || loadFailed) return
    setBusy(true); setError("")
    try {
      const data = await apiFetch<Client>(url, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_confidential: confidential, redirect_uris: redirects.split(/\r?\n/).map((v) => v.trim()).filter(Boolean), allowed_scopes: selected, is_active: active }) })
      setClientId(data.client_id); setSecret(data.client_secret ?? (data.is_confidential ? secret : "")); setDirty(false); setSaved(true)
    } catch (cause) { setError(cause instanceof Error ? cause.message : String(cause)) }
    finally { setBusy(false) }
  }
  async function rotate() {
    if (!window.confirm(t.confirm)) return
    setBusy(true); setError("")
    try {
      const data = await apiFetch<{ client_secret: string }>(`${url}rotate-secret/`, { method: "POST" })
      setSecret(data.client_secret)
    } catch (cause) { setError(cause instanceof Error ? cause.message : String(cause)) }
    finally { setBusy(false) }
  }

  return <Modal open size="lg" hasScrollingContent preventCloseOnClickOutside modalHeading={`${application.name} · ${t.title}`} primaryButtonText={t.save} secondaryButtonText={t.close} primaryButtonDisabled={loading || busy || loadFailed} onRequestClose={close} onSecondarySubmit={close} onRequestSubmit={() => { (document.getElementById("application-oidc-form") as HTMLFormElement | null)?.requestSubmit() }}>
    {loading ? <InlineLoading description={t.loading} /> : <form id="application-oidc-form" className="administration-console__form" onSubmit={(event) => { event.preventDefault(); void save() }}>
      <p>{t.intro}</p>
      {error && <InlineNotification kind="error" title={t.error} subtitle={error} hideCloseButton />}
      {saved && <InlineNotification kind="success" title={t.saved} hideCloseButton />}
      <TextInput id="oidc-client-id" labelText="Client ID" readOnly value={clientId} placeholder={t.generated} />
      {secret && <><InlineNotification kind="info" title={t.secret} subtitle={t.secretHint} hideCloseButton /><TextInput id="oidc-secret" labelText={t.secret} readOnly value={secret} autoComplete="off" /></>}
      <Select id="oidc-type" labelText={t.type} disabled={busy} value={confidential ? "confidential" : "public"} onChange={(event) => { setConfidential(event.target.value === "confidential"); change() }}><SelectItem value="confidential" text={t.confidential} /><SelectItem value="public" text={t.public} /></Select>
      <TextArea id="oidc-redirects" required disabled={busy} labelText={t.redirects} helperText={t.lines} rows={3} value={redirects} onChange={(event) => { setRedirects(event.target.value); change() }} />
      <fieldset disabled={busy}><legend>{t.scopes}</legend>{scopes.map((scope) => <Checkbox key={scope} id={`oidc-scope-${scope}`} labelText={scope} checked={selected.includes(scope)} disabled={scope === "openid" || busy} onChange={(_event, { checked }) => { setSelected((current) => checked ? [...current, scope] : current.filter((value) => value !== scope)); change() }} />)}</fieldset>
      <Toggle id="oidc-active" labelText={t.active} labelA={t.no} labelB={t.yes} toggled={active} disabled={busy} onToggle={(value) => { setActive(value); change() }} />
      {clientId && confidential && <Button type="button" kind="danger--tertiary" disabled={busy || dirty} onClick={() => void rotate()}>{t.rotate}</Button>}
      {clientId && confidential && dirty && <p>{t.unsaved}</p>}
    </form>}
  </Modal>
}
