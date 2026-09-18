import RequireAuth from "@/domains/authentication/components/RequireAuth"

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>
}
