"use client"

import { useLocale } from "./LocaleProvider"

const messages = {
  ca: { appsLoading: "Carregant aplicacions…", appsError: "No s’han pogut carregar les aplicacions.", retry: "Torna-ho a provar", search: "Cerca", notifications: "Notificacions", theme: "Canvia el tema", profile: "Perfil", userProfile: "Perfil d’usuari", apps: "Aplicacions", appSelector: "Selector d’aplicacions", logout: "Tanca la sessió", language: "Idioma", catalan: "Català", spanish: "Castellà", english: "Anglès", kot7kDescription: "Administració d’identitats i aplicacions", skip: "Ves al contingut principal" },
  es: { appsLoading: "Cargando aplicaciones…", appsError: "No se han podido cargar las aplicaciones.", retry: "Volver a intentar", search: "Buscar", notifications: "Notificaciones", theme: "Cambiar el tema", profile: "Perfil", userProfile: "Perfil de usuario", apps: "Aplicaciones", appSelector: "Selector de aplicaciones", logout: "Cerrar sesión", language: "Idioma", catalan: "Catalán", spanish: "Castellano", english: "Inglés", kot7kDescription: "Administración de identidades y aplicaciones", skip: "Ir al contenido principal" },
  en: { appsLoading: "Loading applications…", appsError: "Applications could not be loaded.", retry: "Try again", search: "Search", notifications: "Notifications", theme: "Change theme", profile: "Profile", userProfile: "User profile", apps: "Applications", appSelector: "Application switcher", logout: "Sign out", language: "Language", catalan: "Catalan", spanish: "Spanish", english: "English", kot7kDescription: "Identity and application administration", skip: "Skip to main content" },
}

export function useShellMessages() {
  const { locale } = useLocale()
  return messages[locale]
}
