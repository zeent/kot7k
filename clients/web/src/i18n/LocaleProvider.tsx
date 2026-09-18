"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import type { Locale } from "./types"

const LocaleContext = createContext<{ locale: Locale; setLocale: (locale: Locale) => void } | null>(null)

export function LocaleProvider({ initialLocale, children }: { initialLocale: Locale; children: ReactNode }) {
  const [locale, updateLocale] = useState(initialLocale)
  const router = useRouter()
  const setLocale = useCallback((next: Locale) => {
    if (!["ca", "es", "en"].includes(next)) return
    document.cookie = `kot7k_locale=${next}; Path=/; Max-Age=31536000; SameSite=Lax${location.protocol === "https:" ? "; Secure" : ""}`
    updateLocale(next)
    router.refresh()
  }, [router])
  useEffect(() => { document.documentElement.lang = locale }, [locale])
  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale])
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (!context) throw new Error("useLocale requires LocaleProvider")
  return context
}
