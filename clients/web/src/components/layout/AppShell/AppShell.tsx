"use client"

import type { ReactNode } from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"

import {
  Button,
  Header,
  HeaderGlobalAction,
  HeaderGlobalBar,
  HeaderName,
  HeaderPanel,
  Select,
  SelectItem,
  SkipToContent,
  Theme,
} from "@carbon/react"

import {
  Asleep,
  Light,
  Logout,
  Notification,
  Search,
  Switcher,
  UserAvatar,
} from "@carbon/icons-react"

import ApplicationSwitcher from "@/domains/dashboard/components/ApplicationSwitcher"

import { useLocale } from "@/i18n/LocaleProvider"
import { useShellMessages } from "@/i18n/shell"
import type { Locale } from "@/i18n/types"

import { siteConfig } from "@/config/siteConfig"

import GlobalNotification
  from "@/components/notifications/GlobalNotification"

import NotificationProvider
  from "@/components/notifications/NotificationProvider"

import { useAuth }
  from "@/domains/authentication/context/AuthContext"

import "./AppShell.scss"


export interface AppShellProps {
  children: ReactNode
  headerActions?: ReactNode
  breadcrumbs?: ReactNode
}


type CarbonTheme =
  | "white"
  | "g100"


export function AppShell({
  children,
  headerActions,
  breadcrumbs,
}: AppShellProps) {
  const router =
    useRouter()
  const { locale, setLocale } = useLocale()
  const t = useShellMessages()

  const {
    user,
    signOut,
  } = useAuth()

  const [
    theme,
    setTheme,
  ] = useState<CarbonTheme>(
    "white",
  )

  const [
    isUserPanelOpen,
    setIsUserPanelOpen,
  ] = useState(false)

  const [
    isAppPanelOpen,
    setIsAppPanelOpen,
  ] = useState(false)


  const handleUserPanelToggle =
    () => {
      setIsUserPanelOpen(
        (value) =>
          !value,
      )

      setIsAppPanelOpen(
        false,
      )
    }


  const handleAppPanelToggle =
    () => {
      setIsAppPanelOpen(
        (value) =>
          !value,
      )

      setIsUserPanelOpen(
        false,
      )
    }


  const handleLogout =
    async (): Promise<void> => {
      await signOut()

      router.replace(
        "/authentication/login",
      )
    }


  return (
    <NotificationProvider>
      <Theme theme={theme}>
        <Header
          aria-label={
            siteConfig.name
          }
        >
          <SkipToContent>{t.skip}</SkipToContent>

          <HeaderName
            href="/"
            prefix=""
            className="app-shell__brand"
          >
            <Image
              src="/images/logos/kot7k-menu.png"
              alt={siteConfig.name}
              width={2087}
              height={754}
              priority
              className="app-shell__brand-logo"
            />
          </HeaderName>

          <HeaderGlobalBar>
            {
              headerActions
            }

            <HeaderGlobalAction
              aria-label={t.search}
              tooltipAlignment="end"
            >
              <Search
                size={20}
              />
            </HeaderGlobalAction>

            <HeaderGlobalAction
              aria-label={
                t.notifications
              }
              tooltipAlignment="end"
            >
              <Notification
                size={20}
              />
            </HeaderGlobalAction>

            <HeaderGlobalAction
              aria-label={
                t.theme
              }
              tooltipAlignment="end"
              onClick={() =>
                setTheme(
                  (
                    currentTheme,
                  ) =>
                    currentTheme
                      === "white"
                      ? "g100"
                      : "white",
                )
              }
            >
              {
                theme === "white"
                  ? (
                    <Asleep
                      size={20}
                    />
                  )
                  : (
                    <Light
                      size={20}
                    />
                  )
              }
            </HeaderGlobalAction>

            <HeaderGlobalAction
              aria-label={t.profile}
              tooltipAlignment="end"
              isActive={
                isUserPanelOpen
              }
              onClick={
                handleUserPanelToggle
              }
            >
              <UserAvatar
                size={20}
              />
            </HeaderGlobalAction>

            <HeaderGlobalAction
              aria-label={t.apps}
              tooltipAlignment="end"
              isActive={
                isAppPanelOpen
              }
              onClick={
                handleAppPanelToggle
              }
            >
              <Switcher
                size={20}
              />
            </HeaderGlobalAction>
          </HeaderGlobalBar>

          <HeaderPanel
            aria-label={
              t.userProfile
            }
            expanded={
              isUserPanelOpen
            }
          >
            <div
              style={{
                display:
                  "flex",

                alignItems:
                  "flex-start",

                justifyContent:
                  "space-between",

                gap:
                  "1rem",

                padding:
                  "1rem",

                borderBottom:
                  "1px solid "
                  + "var(--cds-border-subtle-01)",
              }}
            >
              <div
                style={{
                  minWidth: 0,
                  flex: 1,
                }}
              >
                <div
                  style={{
                    fontWeight:
                      600,

                    marginBottom:
                      "0.25rem",
                  }}
                >
                  {
                    user?.full_name
                    || user?.email
                    || "—"
                  }
                </div>

                <div
                  style={{
                    color:
                      "var(--cds-text-secondary)",

                    fontSize:
                      "0.875rem",
                  }}
                >
                  {
                    user?.email
                    || "—"
                  }
                </div>
              </div>

              <Button
                hasIconOnly
                kind="ghost"
                size="sm"
                renderIcon={Logout}
                iconDescription={t.logout}
                tooltipPosition="left"
              onClick={
                handleLogout
              }
              />
            </div>
            <div style={{ padding: "1rem" }}>
              <Select id="kot7k-language" labelText={t.language} value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
                <SelectItem value="ca" text={t.catalan} />
                <SelectItem value="es" text={t.spanish} />
                <SelectItem value="en" text={t.english} />
              </Select>
            </div>
          </HeaderPanel>

          <HeaderPanel
            aria-label={
              t.appSelector
            }
            expanded={
              isAppPanelOpen
            }
          >
            <ApplicationSwitcher open={isAppPanelOpen} onSelect={() => setIsAppPanelOpen(false)} />
          </HeaderPanel>
        </Header>

        <div
          className="app-shell__notification app-shell__notification--collapsed"
        >
          <GlobalNotification />
        </div>

        <main
          id="main-content"
          className="app-shell__main app-shell__main--collapsed"
        >
          {
            breadcrumbs
          }

          {
            children
          }
        </main>
      </Theme>
    </NotificationProvider>
  )
}
