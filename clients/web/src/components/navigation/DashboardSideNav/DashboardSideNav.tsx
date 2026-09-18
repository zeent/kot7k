"use client"

import { SideNavLink } from "@carbon/react"
import { Dashboard as DashboardIcon, Settings } from "@carbon/icons-react"

import { useAuth } from "@/domains/authentication/context/AuthContext"
import { useDashboardMessages } from "@/domains/dashboard/i18n"

export default function DashboardSideNav() {
  const t = useDashboardMessages()
  const { user } = useAuth()
  return <>
    <SideNavLink href="/" renderIcon={DashboardIcon}>{t.dashboard}</SideNavLink>
    {user?.is_staff && <SideNavLink href="/administration" renderIcon={Settings}>{t.administration}</SideNavLink>}
  </>
}
