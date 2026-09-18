import { cookies, headers } from "next/headers"

import { messages, resolveLocale } from "@/i18n/config"
import type { Locale, Messages } from "@/i18n/types"


export async function getRequestLocale(): Promise<Locale> {
  const savedLocale = (await cookies()).get("kot7k_locale")?.value
  if (savedLocale === "ca" || savedLocale === "es" || savedLocale === "en") return savedLocale
  const acceptLanguage = (await headers()).get("accept-language")
  return resolveLocale(acceptLanguage)
}


export async function getRequestMessages(): Promise<Messages> {
  return messages[await getRequestLocale()]
}
