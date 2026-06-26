import { Outlet, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/auth/useAuth"

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    toast.success("Sesión cerrada")
    navigate("/login", { replace: true })
  }

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between border-b bg-card px-6 py-4">
        <div className="flex items-center gap-2 text-lg font-medium">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            ₪
          </span>
          Personal Finance
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">
            {user?.email}
          </span>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Cerrar sesión
          </Button>
        </div>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}
