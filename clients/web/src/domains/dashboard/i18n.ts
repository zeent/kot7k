"use client"

import { useLocale } from "@/i18n/LocaleProvider"

const translations = {
  ca: {
    dashboard: "Inici", administration: "Administració", title: "Bon dia", subtitle: "Aquí tens una visió general del teu entorn KOT7K.",
    overview: "Informació general", users: "Usuaris", applications: "Aplicacions", providers: "Proveïdors d’identitat",
    appWall: "Les meves aplicacions", noApps: "No tens cap aplicació assignada.", openApp: "Obre l’aplicació", roles: "Rols",
    searchApps: "Cerca aplicacions", noAppsFound: "No hi ha aplicacions que coincideixin amb la cerca.", noDescription: "Aquesta aplicació encara no té descripció.",
    kot7kAdministration: "Administració de KOT7K", kot7kAdministrationDescription: "Gestiona usuaris, aplicacions, rols i proveïdors d’identitat.", platformAdministrator: "Administrador de la plataforma",
    activity: "Activitat del compte", noActivity: "Encara no hi ha activitat registrada.", action: "Acció", detail: "Detall", ipAddress: "Adreça IP", date: "Data",
    searchActivity: "Cerca a l’activitat", itemsPerPage: "Elements per pàgina", previousPage: "Pàgina anterior", nextPage: "Pàgina següent",
    login: "Inici de sessió", logout: "Tancament de sessió", roleAssigned: "Rol assignat", roleRemoved: "Rol eliminat", loading: "Carregant el dashboard…", error: "No s’ha pogut carregar el dashboard.",
    loginDetail: "Has iniciat sessió a KOT7K.", logoutDetail: "Has tancat la sessió de KOT7K.", roleAssignedTo: "Rol assignat a", roleRemovedFrom: "Rol eliminat de",
  },
  es: {
    dashboard: "Inicio", administration: "Administración", title: "Buenos días", subtitle: "Aquí tienes una visión general de tu entorno KOT7K.",
    overview: "Información general", users: "Usuarios", applications: "Aplicaciones", providers: "Proveedores de identidad",
    appWall: "Mis aplicaciones", noApps: "No tienes ninguna aplicación asignada.", openApp: "Abrir la aplicación", roles: "Roles",
    searchApps: "Buscar aplicaciones", noAppsFound: "No hay aplicaciones que coincidan con la búsqueda.", noDescription: "Esta aplicación todavía no tiene descripción.",
    kot7kAdministration: "Administración de KOT7K", kot7kAdministrationDescription: "Gestiona usuarios, aplicaciones, roles y proveedores de identidad.", platformAdministrator: "Administrador de la plataforma",
    activity: "Actividad de la cuenta", noActivity: "Todavía no hay actividad registrada.", action: "Acción", detail: "Detalle", ipAddress: "Dirección IP", date: "Fecha",
    searchActivity: "Buscar en la actividad", itemsPerPage: "Elementos por página", previousPage: "Página anterior", nextPage: "Página siguiente",
    login: "Inicio de sesión", logout: "Cierre de sesión", roleAssigned: "Rol asignado", roleRemoved: "Rol eliminado", loading: "Cargando el dashboard…", error: "No se ha podido cargar el dashboard.",
    loginDetail: "Has iniciado sesión en KOT7K.", logoutDetail: "Has cerrado la sesión de KOT7K.", roleAssignedTo: "Rol asignado en", roleRemovedFrom: "Rol eliminado de",
  },
  en: {
    dashboard: "Home", administration: "Administration", title: "Good morning", subtitle: "Here is an overview of your KOT7K environment.",
    overview: "General information", users: "Users", applications: "Applications", providers: "Identity providers",
    appWall: "My applications", noApps: "You have no assigned applications.", openApp: "Open application", roles: "Roles",
    searchApps: "Search applications", noAppsFound: "No applications match your search.", noDescription: "This application does not have a description yet.",
    kot7kAdministration: "KOT7K Administration", kot7kAdministrationDescription: "Manage users, applications, roles, and identity providers.", platformAdministrator: "Platform administrator",
    activity: "Account activity", noActivity: "There is no recorded activity yet.", action: "Action", detail: "Detail", ipAddress: "IP address", date: "Date",
    searchActivity: "Search account activity", itemsPerPage: "Items per page", previousPage: "Previous page", nextPage: "Next page",
    login: "Sign in", logout: "Sign out", roleAssigned: "Role assigned", roleRemoved: "Role removed", loading: "Loading dashboard…", error: "The dashboard could not be loaded.",
    loginDetail: "You signed in to KOT7K.", logoutDetail: "You signed out of KOT7K.", roleAssignedTo: "Role assigned for", roleRemovedFrom: "Role removed from",
  },
} as const

export function useDashboardMessages() {
  const { locale } = useLocale()
  return { ...translations[locale], locale }
}
