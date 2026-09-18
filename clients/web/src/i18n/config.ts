import { ca } from "@/i18n/messages/ca"
import { en } from "@/i18n/messages/en"
import { es } from "@/i18n/messages/es"
import type { Locale, Messages } from "@/i18n/types"


export const fallbackLocale: Locale = "en"

export const supportedLocales: readonly Locale[] = [
  "en",
  "ca",
  "es",
]

export const messages: Record<Locale, Messages> = {
  en,
  ca,
  es,
}


export function resolveLocale(
  acceptLanguage: string | null,
): Locale {
  if (!acceptLanguage) {
    return fallbackLocale
  }

  const preferences = acceptLanguage
    .split(",")
    .map((entry, index) => {
      const [languageTag, ...parameters] = entry.trim().split(";")
      const qualityParameter = parameters.find(
        (parameter) => parameter.trim().startsWith("q="),
      )
      const quality = qualityParameter
        ? Number.parseFloat(qualityParameter.trim().slice(2))
        : 1

      return {
        locale: languageTag.toLowerCase().split("-")[0],
        quality: Number.isFinite(quality) ? quality : 0,
        index,
      }
    })
    .filter((preference) => preference.quality > 0)
    .sort(
      (left, right) =>
        right.quality - left.quality
        || left.index - right.index,
    )

  for (const preference of preferences) {
    if (
      supportedLocales.includes(
        preference.locale as Locale,
      )
    ) {
      return preference.locale as Locale
    }
  }

  return fallbackLocale
}
