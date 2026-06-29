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
import { registerSchema, type RegisterInput } from "@/lib/schemas"
import { extractApiError } from "@/lib/errors"
import { useAuth } from "@/auth/useAuth"

export function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  })

  async function onSubmit(values: RegisterInput) {
    setSubmitError(null)
    try {
      await register({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
      })
      toast.success("Cuenta creada. ¡Bienvenido!")
      navigate("/", { replace: true })
    } catch (err) {
      setSubmitError(
        extractApiError(err) ?? "No pudimos crear tu cuenta",
      )
    }
  }

  const isSubmitting = form.formState.isSubmitting

  return (
    <Card className="border-0 shadow-none sm:border sm:shadow-sm">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl">Crear cuenta</CardTitle>
        <CardDescription>
          Empezá a registrar tus finanzas en menos de un minuto.
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
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nombre</FormLabel>
                    <FormControl>
                      <Input
                        autoComplete="given-name"
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
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Apellido</FormLabel>
                    <FormControl>
                      <Input
                        autoComplete="family-name"
                        disabled={isSubmitting}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
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
                        placeholder="Mínimo 8 caracteres"
                        autoComplete="new-password"
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
            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirmar contraseña</FormLabel>
                  <FormControl>
                    <Input
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      disabled={isSubmitting}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin" />
                  Creando cuenta…
                </>
              ) : (
                "Crear cuenta"
              )}
            </Button>
          </form>
        </Form>
        <p className="mt-6 text-center text-sm text-muted-foreground">
          ¿Ya tenés cuenta?{" "}
          <Link
            to="/login"
            className="font-medium text-foreground underline underline-offset-4 hover:text-primary"
          >
            Iniciá sesión
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
