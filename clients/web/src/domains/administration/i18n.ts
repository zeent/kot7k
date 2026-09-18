"use client"

import { useLocale } from "@/i18n/LocaleProvider"

const translations = {
  ca: {
    title: "Administració", subtitle: "Gestiona el directori, les aplicacions i els accessos de la instal·lació.",
    members: "Usuaris", applications: "Aplicacions", roles: "Rols", assignments: "Assignacions", identityProviders: "Orígens d’identitat",
    addIdentityProvider: "Afegeix origen", providerType: "Tipus", enabled: "Habilitat", disabled: "Deshabilitat", test: "Prova la connexió", edit: "Edita", secret: "Secret o contrasenya", secretHint: "Deixa-ho buit per conservar el secret actual.", configuration: "Configuració", testNever: "No provat", testSuccess: "Connexió correcta", testError: "Error de connexió", update: "Actualitza",
    clientId: "Identificador de client", tenantId: "Identificador del tenant", issuer: "URL de l’emissor", allowedDomains: "Dominis permesos", allowedTenantIds: "Tenants permesos", teamId: "Identificador de l’equip", keyId: "Identificador de la clau", rpId: "Domini WebAuthn", origin: "Origen web", emailHeader: "Capçalera amb el correu", verificationHeader: "Capçalera de verificació", serverUri: "Servidor LDAP", port: "Port", baseDn: "DN base", bindDn: "DN del compte de connexió", userFilter: "Filtre d’usuaris", emailAttribute: "Atribut de correu", firstNameAttribute: "Atribut del nom", lastNameAttribute: "Atribut dels cognoms", scopes: "Scopes",
    addMember: "Afegeix usuari", addApplication: "Crea aplicació", addRole: "Crea rol", addAssignment: "Assigna rol",
    email: "Correu electrònic", role: "Rol", status: "Estat", name: "Nom", key: "Clau", description: "Descripció",
    homepage: "Pàgina principal", application: "Aplicació", member: "Usuari", actions: "Accions", delete: "Elimina",
    cancel: "Cancel·la", create: "Crea", save: "Desa", active: "Actiu", invited: "Convidat", suspended: "Suspès",
    owner: "Propietari", admin: "Administrador", regularMember: "Usuari", loading: "Carregant…", empty: "Encara no hi ha registres.",
    error: "No s’ha pogut completar l’operació.", confirmDelete: "Vols eliminar aquest registre?", search: "Cerca",
  },
  es: {
    title: "Administración", subtitle: "Gestiona el directorio, las aplicaciones y los accesos de la instalación.",
    members: "Usuarios", applications: "Aplicaciones", roles: "Roles", assignments: "Asignaciones", identityProviders: "Orígenes de identidad",
    addIdentityProvider: "Añadir origen", providerType: "Tipo", enabled: "Habilitado", disabled: "Deshabilitado", test: "Probar conexión", edit: "Editar", secret: "Secreto o contraseña", secretHint: "Déjalo vacío para conservar el secreto actual.", configuration: "Configuración", testNever: "No probado", testSuccess: "Conexión correcta", testError: "Error de conexión", update: "Actualizar",
    clientId: "Identificador de cliente", tenantId: "Identificador del tenant", issuer: "URL del emisor", allowedDomains: "Dominios permitidos", allowedTenantIds: "Tenants permitidos", teamId: "Identificador del equipo", keyId: "Identificador de la clave", rpId: "Dominio WebAuthn", origin: "Origen web", emailHeader: "Cabecera con el correo", verificationHeader: "Cabecera de verificación", serverUri: "Servidor LDAP", port: "Puerto", baseDn: "DN base", bindDn: "DN de la cuenta de conexión", userFilter: "Filtro de usuarios", emailAttribute: "Atributo de correo", firstNameAttribute: "Atributo del nombre", lastNameAttribute: "Atributo de los apellidos", scopes: "Scopes",
    addMember: "Añadir usuario", addApplication: "Crear aplicación", addRole: "Crear rol", addAssignment: "Asignar rol",
    email: "Correo electrónico", role: "Rol", status: "Estado", name: "Nombre", key: "Clave", description: "Descripción",
    homepage: "Página principal", application: "Aplicación", member: "Usuario", actions: "Acciones", delete: "Eliminar",
    cancel: "Cancelar", create: "Crear", save: "Guardar", active: "Activo", invited: "Invitado", suspended: "Suspendido",
    owner: "Propietario", admin: "Administrador", regularMember: "Usuario", loading: "Cargando…", empty: "Todavía no hay registros.",
    error: "No se ha podido completar la operación.", confirmDelete: "¿Quieres eliminar este registro?", search: "Buscar",
  },
  en: {
    title: "Administration", subtitle: "Manage this installation's directory, applications, and access.",
    members: "Users", applications: "Applications", roles: "Roles", assignments: "Assignments", identityProviders: "Identity sources",
    addIdentityProvider: "Add source", providerType: "Type", enabled: "Enabled", disabled: "Disabled", test: "Test connection", edit: "Edit", secret: "Secret or password", secretHint: "Leave empty to keep the current secret.", configuration: "Configuration", testNever: "Not tested", testSuccess: "Connection successful", testError: "Connection failed", update: "Update",
    clientId: "Client ID", tenantId: "Tenant ID", issuer: "Issuer URL", allowedDomains: "Allowed domains", allowedTenantIds: "Allowed tenants", teamId: "Team ID", keyId: "Key ID", rpId: "WebAuthn domain", origin: "Web origin", emailHeader: "Email header", verificationHeader: "Verification header", serverUri: "LDAP server", port: "Port", baseDn: "Base DN", bindDn: "Bind account DN", userFilter: "User filter", emailAttribute: "Email attribute", firstNameAttribute: "First-name attribute", lastNameAttribute: "Last-name attribute", scopes: "Scopes",
    addMember: "Add user", addApplication: "Create application", addRole: "Create role", addAssignment: "Assign role",
    email: "Email address", role: "Role", status: "Status", name: "Name", key: "Key", description: "Description",
    homepage: "Homepage", application: "Application", member: "User", actions: "Actions", delete: "Delete",
    cancel: "Cancel", create: "Create", save: "Save", active: "Active", invited: "Invited", suspended: "Suspended",
    owner: "Owner", admin: "Administrator", regularMember: "User", loading: "Loading…", empty: "There are no records yet.",
    error: "The operation could not be completed.", confirmDelete: "Do you want to delete this record?", search: "Search",
  },
} as const

export function useAdministrationMessages() {
  const { locale } = useLocale()
  return translations[locale]
}
