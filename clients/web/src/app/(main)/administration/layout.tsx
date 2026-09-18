import type { ReactNode } from "react"
import { AppShell } from "@/components/layout/AppShell/AppShell"

export default function AdministrationLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>
}
