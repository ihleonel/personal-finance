import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { loginSchema, type LoginInput } from "@/lib/schemas"
import { ApiError } from "@/lib/api"
import { useAuth } from "@/auth/useAuth"

function extractApiError(err: unknown): string | null {
  if (!(err instanceof ApiError)) return null
  const data = err.data
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === "string") return detail
  }
  return err.message
}

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  })

  async function onSubmit(values: LoginInput) {
    setSubmitError(null)
    try {
      await login(values.email, values.password)
      toast.success("Sesión iniciada")
      navigate("/", { replace: true })
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos iniciar sesión")
    }
  }

  const isSubmitting = form.formState.isSubmitting

  return (
    <Card className="border-0 shadow-none sm:border sm:shadow-sm">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl">Iniciar sesión</CardTitle>
        <CardDescription>
          Ingresá tu email y contraseña para acceder.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {submitError ? (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        ) : null}
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="vos@ejemplo.com"
                      autoComplete="email"
                      disabled={isSubmitting}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contraseña</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        autoComplete="current-password"
                        disabled={isSubmitting}
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        className="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground hover:text-foreground"
                        tabIndex={-1}
                        aria-label={
                          showPassword
                            ? "Ocultar contraseña"
                            : "Mostrar contraseña"
                        }
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin" />
                  Iniciando sesión…
                </>
              ) : (
                "Iniciar sesión"
              )}
            </Button>
          </form>
        </Form>
        <p className="mt-6 text-center text-sm text-muted-foreground">
          ¿No tenés cuenta?{" "}
          <Link
            to="/register"
            className="font-medium text-foreground underline underline-offset-4 hover:text-primary"
          >
            Registrate
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
