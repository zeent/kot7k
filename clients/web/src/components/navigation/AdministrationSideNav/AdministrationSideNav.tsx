"use client"

import { SideNavLink } from "@carbon/react"
import { App, UserMultiple } from "@carbon/icons-react"

import { useAdministrationMessages } from "@/domains/administration/i18n"


export default function AdministrationSideNav() {
  const t = useAdministrationMessages()
  return <>
    <SideNavLink href="/administration" renderIcon={UserMultiple}>{t.title}</SideNavLink>
    <SideNavLink href="/administration#applications" renderIcon={App}>{t.applications}</SideNavLink>
  </>
}
