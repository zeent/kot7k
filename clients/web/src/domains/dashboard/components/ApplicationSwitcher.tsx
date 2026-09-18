"use client"

import { useEffect, useState } from "react"
import { Button, InlineLoading, InlineNotification } from "@carbon/react"
import { App } from "@carbon/icons-react"
import { useAuth } from "@/domains/authentication/context/AuthContext"
import { useShellMessages } from "@/i18n/shell"
import { useDashboardMessages } from "../i18n"
import { getDashboard } from "../services"
import type { DashboardApplication } from "../types"

export default function ApplicationSwitcher({ open, onSelect }: { open: boolean; onSelect: () => void }) {
  const { user } = useAuth()
  const t = useDashboardMessages()
  const shell = useShellMessages()
  const [applications, setApplications] = useState<DashboardApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    if (!open || !user) return
    let cancelled = false
    const timeout = window.setTimeout(() => {
      setLoading(true)
      setFailed(false)
      getDashboard().then((data) => {
        if (!cancelled) setApplications(data.applications)
      }).catch(() => {
        if (!cancelled) { setFailed(true); setApplications([]) }
      }).finally(() => { if (!cancelled) setLoading(false) })
    }, 0)
    return () => { cancelled = true; window.clearTimeout(timeout) }
  }, [open, user, attempt])

  if (!open) return null
  if (loading) return <div style={{ padding: "1rem" }}><InlineLoading description={shell.appsLoading} /></div>
  if (failed) return <div style={{ padding: "1rem" }}><InlineNotification kind="error" title={shell.appsError} hideCloseButton lowContrast /><Button kind="ghost" onClick={() => setAttempt((value) => value + 1)}>{shell.retry}</Button></div>
  if (!applications.length) return <p style={{ padding: "1rem" }}>{t.noApps}</p>

  return <>{applications.map((application) => {
    const administration = application.key === "kot7k-administration"
    const name = administration ? t.kot7kAdministration : application.name
    const description = administration ? t.kot7kAdministrationDescription : application.description || t.noDescription
    const content = <><App size={20} /><span><strong>{name}</strong><br />{description}</span></>
    return application.homepage_url
      ? <a key={application.id} href={application.homepage_url} className="app-shell__user-menu-item" onClick={onSelect}>{content}</a>
      : <button key={application.id} type="button" disabled className="app-shell__user-menu-item">{content}</button>
  })}</>
}
