import { Navigate, Outlet } from "react-router-dom"
import { useAuth } from "@/auth/useAuth"

export function GuestRoute() {
  const { status } = useAuth()

  if (status === "loading") {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="text-sm text-muted-foreground">Cargando…</p>
      </div>
    )
  }

  if (status === "authed") {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
