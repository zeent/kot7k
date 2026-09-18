"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from "react"
import { resolveLocale, supportedLocales } from "./config"
import type { Locale } from "./types"

const LocaleContext = createContext<{ locale: Locale; setLocale: (locale: Locale) => void } | null>(null)

// The server snapshot keeps the initial client render identical to the export.
const subscribe = () => () => {}

function getBrowserLocale(): Locale {
  const savedLocale = document.cookie.split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith("kot7k_locale="))
    ?.slice("kot7k_locale=".length)
  return supportedLocales.includes(savedLocale as Locale)
    ? savedLocale as Locale
    : resolveLocale(navigator.languages.join(","))
}

export function LocaleProvider({ initialLocale, children }: { initialLocale: Locale; children: ReactNode }) {
  const hydrated = useSyncExternalStore(subscribe, () => true, () => false)
  const [selectedLocale, updateLocale] = useState<Locale | null>(null)
  const locale = selectedLocale ?? (hydrated ? getBrowserLocale() : initialLocale)
  const setLocale = useCallback((next: Locale) => {
    if (!["ca", "es", "en"].includes(next)) return
    document.cookie = `kot7k_locale=${next}; Path=/; Max-Age=31536000; SameSite=Lax${location.protocol === "https:" ? "; Secure" : ""}`
    updateLocale(next)
  }, [])
  useEffect(() => { document.documentElement.lang = locale }, [locale])
  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale])
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (!context) throw new Error("useLocale requires LocaleProvider")
  return context
}
