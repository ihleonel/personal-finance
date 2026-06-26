import { Outlet } from "react-router-dom"

export function AuthLayout() {
  return (
    <div className="grid min-h-svh w-full lg:grid-cols-2">
      <div className="relative hidden flex-col justify-center gap-12 bg-muted p-10 lg:flex">
        <div className="flex items-center gap-2 text-lg font-medium">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            ₪
          </span>
          Personal Finance
        </div>
        <div className="space-y-2">
          <p className="text-2xl font-semibold tracking-tight">
            Tomá el control de tu dinero.
          </p>
          <p className="text-sm text-muted-foreground">
            Registrá tus ingresos y gastos, seguí tu balance y alcanzá tus
            objetivos financieros mes a mes.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center justify-center gap-2 text-lg font-medium lg:hidden">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              ₪
            </span>
            Personal Finance
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
