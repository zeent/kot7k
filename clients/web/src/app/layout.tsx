import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.scss";
import { siteConfig } from "@/config/siteConfig"

import { AuthProvider }
  from "@/domains/authentication/context/AuthContext"
import { LocaleProvider } from "@/i18n/LocaleProvider"
import { getRequestLocale } from "@/i18n/server"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: siteConfig.name,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getRequestLocale()

  return (
    <html lang={locale} className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
      <LocaleProvider initialLocale={locale}>
      <AuthProvider>
        {children}
      </AuthProvider>
      </LocaleProvider>
      </body>
    </html>
  );
}
