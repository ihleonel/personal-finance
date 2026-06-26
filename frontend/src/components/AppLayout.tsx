import { Outlet } from "react-router-dom"
import { UserMenu } from "@/components/UserMenu"

export function AppLayout() {
  return (
    <div className="flex min-h-svh">
      <aside className="hidden w-64 shrink-0 flex-col justify-between border-r bg-card p-6 md:flex">
        <div className="flex flex-col gap-6">
          <div className="flex items-center gap-2 text-lg font-medium">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              ₪
            </span>
            Personal Finance
          </div>
        </div>
        <UserMenu variant="desktop" />
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-card px-6 py-4 md:hidden">
          <div className="flex items-center gap-2 text-lg font-medium">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              ₪
            </span>
            Personal Finance
          </div>
          <UserMenu variant="compact" />
        </header>
        <main className="flex-1 p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}