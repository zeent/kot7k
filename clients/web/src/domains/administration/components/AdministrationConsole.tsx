"use client"

import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react"
import { Button, DataTable, InlineLoading, InlineNotification, Layer, Modal, Select, SelectItem, Tab, TabList, TabPanel, TabPanels, Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow, TableToolbar, TableToolbarContent, TableToolbarSearch, Tabs, TextArea, TextInput } from "@carbon/react"
import { Add, Edit, TrashCan } from "@carbon/icons-react"

import PageHeader from "@/components/layout/PageHeader/PageHeader"
import { createApplication, createAssignment, createUser, createRole, deleteApplication, deleteAssignment, deleteUser, deleteRole, listApplications, listAssignments, listUsers, listRoles, updateApplication } from "../services"
import type { ApplicationAssignment, ApplicationRole, DirectoryUser, ManagedApplication } from "../types"
import { useAdministrationMessages } from "../i18n"
import "./AdministrationConsole.scss"
import IdentityProvidersPanel from "./IdentityProvidersPanel"
import ApplicationOIDC from "./ApplicationOIDC"

type Dialog = "member" | "application" | "role" | "assignment" | null

export default function AdministrationConsole() {
  const t = useAdministrationMessages()
  const [members, setMembers] = useState<DirectoryUser[]>([])
  const [applications, setApplications] = useState<ManagedApplication[]>([])
  const [roles, setRoles] = useState<ApplicationRole[]>([])
  const [assignments, setAssignments] = useState<ApplicationAssignment[]>([])
  const [oidcApplication, setOIDCApplication] = useState<ManagedApplication | null>(null)
  const [dialog, setDialog] = useState<Dialog>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState("")
  const [userIsStaff, setUserIsStaff] = useState(false)
  const [userIsActive, setUserIsActive] = useState(true)
  const [applicationId, setApplicationId] = useState("")
  const [userId, setUserId] = useState("")
  const [roleId, setRoleId] = useState("")
  const [key, setKey] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [homepage, setHomepage] = useState("")
  const [editingApplicationId, setEditingApplicationId] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      const [nextMembers, nextApplications, nextRoles, nextAssignments] = await Promise.all([
        listUsers(), listApplications(), listRoles(), listAssignments(),
      ])
      setMembers(nextMembers)
      setApplications(nextApplications)
      setRoles(nextRoles)
      setAssignments(nextAssignments)
      setError(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t.error)
    } finally {
      setLoading(false)
    }
  }, [t.error])

  useEffect(() => {
    const timeout = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timeout)
  }, [load])

  const availableRoles = useMemo(
    () => roles.filter((role) => role.application === Number(applicationId)),
    [applicationId, roles],
  )

  function open(nextDialog: Exclude<Dialog, null>) {
    setDialog(nextDialog)
    setError(null)
    setEmail("")
    setUserIsStaff(false)
    setUserIsActive(true)
    setApplicationId(applications[0]?.id.toString() ?? "")
    setUserId(members[0]?.id.toString() ?? "")
    setRoleId("")
    setKey("")
    setName("")
    setDescription("")
    setHomepage("")
    setEditingApplicationId(null)
  }

  function editApplication(application: ManagedApplication) {
    setDialog("application")
    setEditingApplicationId(application.id)
    setKey(application.key)
    setName(application.name)
    setDescription(application.description)
    setHomepage(application.homepage_url)
    setError(null)
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!dialog) return
    setSaving(true)
    try {
      if (dialog === "member") await createUser(email, userIsStaff, userIsActive)
      if (dialog === "application") {
        const body = { key, name, description, homepage_url: homepage }
        if (editingApplicationId) await updateApplication(editingApplicationId, body)
        else setOIDCApplication(await createApplication(body))
      }
      if (dialog === "role") await createRole(Number(applicationId), key, name, description)
      if (dialog === "assignment") await createAssignment(Number(applicationId), Number(userId), Number(roleId))
      setDialog(null)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t.error)
    } finally {
      setSaving(false)
    }
  }

  async function remove(action: () => Promise<void>) {
    if (!window.confirm(t.confirmDelete)) return
    try {
      await action()
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t.error)
    }
  }

  const roleLabel = (isStaff: boolean) => isStaff ? t.admin : t.regularMember
  const statusLabel = (isActive: boolean) => isActive ? t.active : t.suspended

  return (
    <div className="administration-console">
      <PageHeader title={t.title} subtitle={t.subtitle} />
      {error && <InlineNotification kind="error" lowContrast title={t.error} subtitle={error} onClose={() => setError(null)} />}
      {loading ? <InlineLoading description={t.loading} /> : (
        <div className="administration-console__tabs">
          <Tabs>
          <TabList aria-label={t.title} contained>
            <Tab>{t.members}</Tab><Tab>{t.applications}</Tab><Tab>{t.roles}</Tab><Tab>{t.assignments}</Tab><Tab>{t.identityProviders}</Tab>
          </TabList>
          <TabPanels>
            <TabPanel><Section title={t.members} action={t.addMember} onAdd={() => open("member")}>
              <AdministrationDataTable
                title={t.members}
                action={t.addMember}
                searchLabel={`${t.search}: ${t.members}`}
                onAdd={() => open("member")}
                headers={[{ key: "email", header: t.email }, { key: "role", header: t.role }, { key: "status", header: t.status }, { key: "actions", header: t.actions }]}
                rows={members.map((member) => ({ id: String(member.id), searchText: `${member.email} ${member.full_name} ${roleLabel(member.is_staff)} ${statusLabel(member.is_active)}`, email: member.email, role: roleLabel(member.is_staff), status: <Status value={statusLabel(member.is_active)} active={member.is_active} />, actions: <DeleteButton label={t.delete} onClick={() => void remove(() => deleteUser(member.id))} /> }))}
                empty={t.empty}
              />
            </Section></TabPanel>
            <TabPanel><Section title={t.applications} action={t.addApplication} onAdd={() => open("application")}>
              <AdministrationDataTable
                title={t.applications}
                action={t.addApplication}
                searchLabel={`${t.search}: ${t.applications}`}
                onAdd={() => open("application")}
                headers={[{ key: "name", header: t.name }, { key: "key", header: t.key }, { key: "homepage", header: t.homepage }, { key: "status", header: t.status }, { key: "actions", header: t.actions }]}
                rows={applications.map((application) => ({ id: String(application.id), searchText: `${application.name} ${application.key} ${application.description} ${application.homepage_url}`, name: <div className="administration-console__primary"><strong>{application.name}</strong>{application.description && <small>{application.description}</small>}</div>, key: <code>{application.key}</code>, homepage: application.homepage_url || "—", status: <Status value={application.is_active ? t.active : t.suspended} active={application.is_active} />, actions: <><Button hasIconOnly kind="ghost" size="sm" renderIcon={Edit} iconDescription={t.edit} onClick={() => editApplication(application)} /><Button kind="ghost" size="sm" onClick={() => setOIDCApplication(application)}>OpenID Connect</Button><DeleteButton label={t.delete} onClick={() => void remove(() => deleteApplication(application.id))} /></> }))}
                empty={t.empty}
              />
            </Section></TabPanel>
            <TabPanel><Section title={t.roles} action={t.addRole} onAdd={() => open("role")} disabled={applications.length === 0}>
              <AdministrationDataTable
                title={t.roles}
                action={t.addRole}
                searchLabel={`${t.search}: ${t.roles}`}
                onAdd={() => open("role")}
                addDisabled={applications.length === 0}
                headers={[{ key: "name", header: t.name }, { key: "key", header: t.key }, { key: "application", header: t.application }, { key: "description", header: t.description }, { key: "actions", header: t.actions }]}
                rows={roles.map((role) => ({ id: String(role.id), searchText: `${role.name} ${role.key} ${role.application_name} ${role.description}`, name: <strong>{role.name}</strong>, key: <code>{role.key}</code>, application: role.application_name, description: role.description || "—", actions: <DeleteButton label={t.delete} onClick={() => void remove(() => deleteRole(role.id))} /> }))}
                empty={t.empty}
              />
            </Section></TabPanel>
            <TabPanel><Section title={t.assignments} action={t.addAssignment} onAdd={() => open("assignment")} disabled={!applications.length || !members.length || !roles.length}>
              <AdministrationDataTable
                title={t.assignments}
                action={t.addAssignment}
                searchLabel={`${t.search}: ${t.assignments}`}
                onAdd={() => open("assignment")}
                addDisabled={!applications.length || !members.length || !roles.length}
                headers={[{ key: "member", header: t.member }, { key: "application", header: t.application }, { key: "role", header: t.role }, { key: "actions", header: t.actions }]}
                rows={assignments.map((assignment) => ({ id: String(assignment.id), searchText: `${assignment.user_email} ${assignment.application_name} ${assignment.role_name}`, member: assignment.user_email, application: assignment.application_name, role: assignment.role_name, actions: <DeleteButton label={t.delete} onClick={() => void remove(() => deleteAssignment(assignment.id))} /> }))}
                empty={t.empty}
              />
            </Section></TabPanel>
            <TabPanel><Section title={t.identityProviders} action={t.addIdentityProvider} onAdd={() => undefined}>
              <IdentityProvidersPanel />
            </Section></TabPanel>
          </TabPanels>
          </Tabs>
        </div>
      )}

      {oidcApplication && <ApplicationOIDC key={oidcApplication.id} application={oidcApplication} onClose={() => setOIDCApplication(null)} />}
      <Modal open={dialog !== null} modalHeading={dialog === "member" ? t.addMember : dialog === "application" ? editingApplicationId ? t.edit : t.addApplication : dialog === "role" ? t.addRole : t.addAssignment} primaryButtonText={editingApplicationId ? t.update : t.create} secondaryButtonText={t.cancel} primaryButtonDisabled={saving} onRequestClose={() => setDialog(null)} onRequestSubmit={() => { (document.getElementById("administration-dialog-form") as HTMLFormElement | null)?.requestSubmit() }}>
        <form id="administration-dialog-form" className="administration-console__form" onSubmit={(event) => void submit(event)}>
          {dialog === "member" && <><TextInput id="member-email" type="email" required labelText={t.email} value={email} onChange={(event) => setEmail(event.target.value)} /><Select id="member-role" labelText={t.role} value={userIsStaff ? "admin" : "user"} onChange={(event) => setUserIsStaff(event.target.value === "admin")}><SelectItem value="user" text={t.regularMember} /><SelectItem value="admin" text={t.admin} /></Select><Select id="member-status" labelText={t.status} value={userIsActive ? "active" : "suspended"} onChange={(event) => setUserIsActive(event.target.value === "active")}><SelectItem value="active" text={t.active} /><SelectItem value="suspended" text={t.suspended} /></Select></>}
          {dialog === "application" && <><TextInput id="application-name" required labelText={t.name} value={name} onChange={(event) => setName(event.target.value)} /><TextInput id="application-key" required labelText={t.key} value={key} onChange={(event) => setKey(event.target.value.toLowerCase())} /><TextInput id="application-homepage" type="url" labelText={t.homepage} value={homepage} onChange={(event) => setHomepage(event.target.value)} /><TextArea id="application-description" labelText={t.description} value={description} onChange={(event) => setDescription(event.target.value)} /></>}
          {dialog === "role" && <><ApplicationSelect label={t.application} applications={applications} value={applicationId} onChange={setApplicationId} /><TextInput id="role-name" required labelText={t.name} value={name} onChange={(event) => setName(event.target.value)} /><TextInput id="role-key" required labelText={t.key} value={key} onChange={(event) => setKey(event.target.value.toLowerCase())} /><TextArea id="role-description" labelText={t.description} value={description} onChange={(event) => setDescription(event.target.value)} /></>}
          {dialog === "assignment" && <><ApplicationSelect label={t.application} applications={applications} value={applicationId} onChange={(value) => { setApplicationId(value); setRoleId("") }} /><Select id="assignment-member" required labelText={t.member} value={userId} onChange={(event) => setUserId(event.target.value)}>{members.map((member) => <SelectItem key={member.id} value={member.id.toString()} text={member.email} />)}</Select><Select id="assignment-role" required labelText={t.role} value={roleId} onChange={(event) => setRoleId(event.target.value)}><SelectItem value="" text="—" />{availableRoles.map((role) => <SelectItem key={role.id} value={role.id.toString()} text={role.name} />)}</Select></>}
        </form>
      </Modal>
    </div>
  )
}

function Section({ children }: { title: string; action: string; onAdd: () => void; disabled?: boolean; children: React.ReactNode }) {
  return <section className="administration-console__section">{children}</section>
}

type AdministrationTableRow = { id: string } & Record<string, ReactNode>
type AdministrationTableHeader = { key: string; header: string }

function AdministrationDataTable({ title, action, searchLabel, onAdd, addDisabled = false, headers, rows, empty }: { title: string; action: string; searchLabel: string; onAdd: () => void; addDisabled?: boolean; headers: AdministrationTableHeader[]; rows: AdministrationTableRow[]; empty: string }) {
  const [search, setSearch] = useState("")
  const normalizedSearch = search.trim().toLocaleLowerCase()
  const filteredRows = normalizedSearch
    ? rows.filter((row) => String(row.searchText ?? "").toLocaleLowerCase().includes(normalizedSearch))
    : rows

  return <DataTable rows={filteredRows} headers={headers}>
    {({ rows: carbonRows, headers: carbonHeaders, getHeaderProps, getRowProps, getTableProps }) => (
      <Layer level={1}>
        <TableContainer aria-label={title}>
          <TableToolbar>
            <TableToolbarContent>
              <TableToolbarSearch
                persistent
                placeholder={searchLabel}
                value={search}
                onChange={(_event, value) => setSearch(value ?? "")}
              />
              <Button renderIcon={Add} disabled={addDisabled} onClick={onAdd}>
                {action}
              </Button>
            </TableToolbarContent>
          </TableToolbar>
          <Table {...getTableProps()}>
            <TableHead>
              <TableRow>
                {carbonHeaders.map((header) => {
                  const props = getHeaderProps({ header })
                  return <TableHeader {...props} key={props.key}>{header.header}</TableHeader>
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {carbonRows.length === 0 ? (
                <TableRow><TableCell colSpan={carbonHeaders.length}>{empty}</TableCell></TableRow>
              ) : carbonRows.map((row) => {
                const props = getRowProps({ row })
                return <TableRow {...props} key={props.key}>
                  {row.cells.map((cell) => <TableCell key={cell.id}>{cell.value}</TableCell>)}
                </TableRow>
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Layer>
    )}
  </DataTable>
}

function Status({ value, active }: { value: string; active: boolean }) { return <span className={`administration-console__status ${active ? "administration-console__status--active" : ""}`}>{value}</span> }
function DeleteButton({ label, onClick }: { label: string; onClick: () => void }) { return <Button hasIconOnly kind="ghost" size="sm" renderIcon={TrashCan} iconDescription={label} onClick={onClick} /> }
function ApplicationSelect({ label, applications, value, onChange }: { label: string; applications: ManagedApplication[]; value: string; onChange: (value: string) => void }) { return <Select id={`application-${label}`} required labelText={label} value={value} onChange={(event) => onChange(event.target.value)}>{applications.map((application) => <SelectItem key={application.id} value={application.id.toString()} text={application.name} />)}</Select> }
