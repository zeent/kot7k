"use client"

import { useEffect, useMemo, useState } from "react"
import { App, ArrowUpRight, Events, UserIdentification, UserMultiple } from "@carbon/icons-react"
import { ClickableTile, DataTable, DataTableSkeleton, InlineNotification, Pagination, Search, Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow, TableToolbar, TableToolbarContent, TableToolbarSearch, Tag, Tile } from "@carbon/react"

import PageHeader from "@/components/layout/PageHeader/PageHeader"
import { useAuth } from "@/domains/authentication/context/AuthContext"
import { useDashboardMessages } from "../i18n"
import { getDashboard } from "../services"
import type { AccountActivity, DashboardData } from "../types"
import "./Dashboard.scss"

const APP_MARK_COLORS = [
  "var(--cds-blue-60, #0f62fe)",
  "var(--cds-purple-60, #8a3ffc)",
  "var(--cds-magenta-60, #d02670)",
  "var(--cds-red-60, #da1e28)",
  "var(--cds-teal-60, #007d79)",
  "var(--cds-cyan-60, #0072c3)",
  "var(--cds-green-60, #198038)",
] as const

function appMarkColor(initials: string): string {
  const hash = Array.from(initials).reduce(
    (value, character) => ((value * 31) + character.charCodeAt(0)) >>> 0,
    0,
  )
  return APP_MARK_COLORS[hash % APP_MARK_COLORS.length]
}

export default function Dashboard() {
  const t = useDashboardMessages()
  const { user } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [applicationSearch, setApplicationSearch] = useState("")
  const [activitySearch, setActivitySearch] = useState("")
  const [activityPage, setActivityPage] = useState(1)
  const [activityPageSize, setActivityPageSize] = useState(10)

  useEffect(() => {
    let cancelled = false
    void getDashboard().then((result) => { if (!cancelled) setData(result) }).catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : t.error) })
    return () => { cancelled = true }
  }, [t.error])

  const actionLabel = (activity: AccountActivity) => activity.action === "login" ? t.login : activity.action === "logout" ? t.logout : activity.action === "role_assigned" ? t.roleAssigned : t.roleRemoved
  const activityDetail = (activity: AccountActivity) => {
    if (activity.action === "login") return t.loginDetail
    if (activity.action === "logout") return t.logoutDetail
    const role = String(activity.metadata.role ?? "")
    const application = String(activity.metadata.application ?? "")
    return `${role} · ${activity.action === "role_assigned" ? t.roleAssignedTo : t.roleRemovedFrom} ${application}`
  }
  const activityRows = (data?.activities ?? []).map((activity) => ({ id: String(activity.id), action: actionLabel(activity), detail: activityDetail(activity), ip: activity.ip_address ?? "—", date: new Intl.DateTimeFormat(t.locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(activity.created_at)) }))
  const headers = [{ key: "action", header: t.action }, { key: "detail", header: t.detail }, { key: "ip", header: t.ipAddress }, { key: "date", header: t.date }]
  const filteredActivityRows = useMemo(() => {
    const needle = activitySearch.trim().toLocaleLowerCase()
    return needle
      ? activityRows.filter((row) => `${row.action} ${row.detail} ${row.ip} ${row.date}`.toLocaleLowerCase().includes(needle))
      : activityRows
  }, [activityRows, activitySearch])
  const paginatedActivityRows = filteredActivityRows.slice(
    (activityPage - 1) * activityPageSize,
    activityPage * activityPageSize,
  )
  const visibleApplications = useMemo(() => {
    const needle = applicationSearch.trim().toLocaleLowerCase()
    if (!needle) return data?.applications ?? []
    return (data?.applications ?? []).filter((application) =>
      `${application.name} ${application.key} ${application.description} ${application.roles.map((role) => role.name).join(" ")}`
        .toLocaleLowerCase().includes(needle),
    )
  }, [applicationSearch, data?.applications])

  return <div className="kot7k-dashboard">
    <PageHeader title={`${t.title}${user?.first_name ? `, ${user.first_name}` : ""}`} subtitle={t.subtitle} />
    {error && <InlineNotification kind="error" lowContrast title={t.error} subtitle={error} />}
    {!data ? <DataTableSkeleton columnCount={3} rowCount={4} showHeader={false} /> : <>
      <section aria-labelledby="overview-title">
        <h2 id="overview-title" className="kot7k-dashboard__section-title">{t.overview}</h2>
        <div className="kot7k-dashboard__metrics">
          <MetricTile label={t.users} value={data.metrics.users} icon={<UserMultiple size={28} />} accent="blue" />
          <MetricTile label={t.applications} value={data.metrics.applications} icon={<App size={28} />} accent="purple" />
          <MetricTile label={t.providers} value={data.metrics.identity_providers} icon={<UserIdentification size={28} />} accent="teal" />
        </div>
      </section>

      <section aria-labelledby="apps-title">
        <h2 id="apps-title" className="kot7k-dashboard__section-title">{t.appWall}</h2>
        <Search id="dashboard-application-search" size="lg" labelText={t.searchApps} placeholder={t.searchApps} value={applicationSearch} onChange={(event) => setApplicationSearch(event.target.value)} />
        {visibleApplications.length === 0 ? <Tile className="kot7k-dashboard__empty">{data.applications.length ? t.noAppsFound : t.noApps}</Tile> : <div className="kot7k-dashboard__app-wall">
          {visibleApplications.map((application) => {
            const isKOT7KAdministration = application.key === "kot7k-administration"
            const applicationName = isKOT7KAdministration ? t.kot7kAdministration : application.name
            const description = isKOT7KAdministration ? t.kot7kAdministrationDescription : application.description || t.noDescription
            const initials = applicationName.slice(0, 2).toUpperCase()
            return <ClickableTile key={application.id} href={application.homepage_url || undefined} disabled={!application.homepage_url} className="kot7k-dashboard__app">
              <div className="kot7k-dashboard__app-top"><span className="kot7k-dashboard__app-mark" style={{ backgroundColor: appMarkColor(initials) }}>{initials}</span>{application.homepage_url && <ArrowUpRight size={20} aria-label={t.openApp} />}</div>
              <h3>{applicationName}</h3><p>{description}</p>
              <div className="kot7k-dashboard__roles" aria-label={t.roles}>{application.roles.map((role) => <Tag key={role.key} type="blue" size="sm">{isKOT7KAdministration ? t.platformAdministrator : role.name}</Tag>)}</div>
            </ClickableTile>
          })}
        </div>}
      </section>

      <section aria-labelledby="activity-title">
        <h2 id="activity-title" className="kot7k-dashboard__section-title"><Events size={20} />{t.activity}</h2>
        <DataTable rows={paginatedActivityRows} headers={headers}>{({ rows, headers: carbonHeaders, getHeaderProps, getRowProps, getTableProps }) => <TableContainer>
          <TableToolbar><TableToolbarContent><TableToolbarSearch persistent placeholder={t.searchActivity} value={activitySearch} onChange={(_event, value) => { setActivitySearch(value ?? ""); setActivityPage(1) }} /></TableToolbarContent></TableToolbar>
          <Table {...getTableProps()}><TableHead><TableRow>{carbonHeaders.map((header) => { const props = getHeaderProps({ header }); return <TableHeader {...props} key={props.key}>{header.header}</TableHeader> })}</TableRow></TableHead>
            <TableBody>{rows.length ? rows.map((row) => { const props = getRowProps({ row }); return <TableRow {...props} key={props.key}>{row.cells.map((cell) => <TableCell key={cell.id}>{cell.value}</TableCell>)}</TableRow> }) : <TableRow><TableCell colSpan={4}>{t.noActivity}</TableCell></TableRow>}</TableBody>
          </Table>
          <Pagination page={activityPage} pageSize={activityPageSize} pageSizes={[5, 10, 20]} totalItems={filteredActivityRows.length} itemsPerPageText={t.itemsPerPage} backwardText={t.previousPage} forwardText={t.nextPage} onChange={({ page, pageSize }) => { setActivityPage(page); setActivityPageSize(pageSize) }} />
        </TableContainer>}</DataTable>
      </section>
    </>}
  </div>
}

function MetricTile({ label, value, icon, accent }: { label: string; value: number; icon: React.ReactNode; accent: "blue" | "purple" | "teal" }) {
  return <Tile className={`kot7k-dashboard__metric kot7k-dashboard__metric--${accent}`}><div className="kot7k-dashboard__metric-icon">{icon}</div><strong>{value.toLocaleString()}</strong><span>{label}</span></Tile>
}
