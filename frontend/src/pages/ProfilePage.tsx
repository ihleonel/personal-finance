import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { ArrowLeft, Loader2, Lock } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
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
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/auth/useAuth"
import { ApiError, fetchCurrentUser } from "@/lib/api"
import { profileSchema, type ProfileInput } from "@/lib/schemas"

function extractApiError(err: unknown): string | null {
  if (!(err instanceof ApiError)) return null
  const data = err.data
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === "string") return detail
    const nonField = (data as { non_field_errors?: unknown }).non_field_errors
    if (Array.isArray(nonField) && typeof nonField[0] === "string") {
      return nonField[0]
    }
  }
  return err.message
}

export function ProfilePage() {
  const { user, status, updateProfile } = useAuth()
  const navigate = useNavigate()
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (status === "authed" && !user) {
      fetchCurrentUser().catch(() => undefined)
    }
  }, [status, user])

  const form = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
    },
    values: user
      ? { first_name: user.first_name, last_name: user.last_name }
      : undefined,
  })

  const isSubmitting = form.formState.isSubmitting
  const isDirty = form.formState.isDirty
  const isValid = form.formState.isValid

  async function onSubmit(values: ProfileInput) {
    setSubmitError(null)
    try {
      await updateProfile(values)
      toast.success("Perfil actualizado")
    } catch (err) {
      setSubmitError(
        extractApiError(err) ?? "No pudimos actualizar tu perfil",
      )
    }
  }

  function handleCancel() {
    form.reset({
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
    })
    setSubmitError(null)
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-2xl">
        <p className="text-sm text-muted-foreground">Cargando perfil…</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Mi perfil</h1>
        <p className="text-muted-foreground">
          Información de tu cuenta.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Datos personales</CardTitle>
          <CardDescription>
            Editá tu nombre y apellido. El email no se puede modificar.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {submitError ? (
            <Alert variant="destructive">
              <AlertDescription>{submitError}</AlertDescription>
            </Alert>
          ) : null}
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4"
            >
              <div className="grid gap-4 sm:grid-cols-2">
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

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Email
                  </span>
                  <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Lock className="h-3.5 w-3.5" />
                    {user.email}
                  </span>
                </div>
                <div className="grid gap-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Estado
                  </span>
                  <span>
                    <span
                      className={
                        user.is_active
                          ? "inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
                          : "inline-flex items-center rounded-full bg-destructive/10 px-2.5 py-0.5 text-xs font-medium text-destructive"
                      }
                    >
                      {user.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-2">
                <Button
                  type="submit"
                  disabled={isSubmitting || !isDirty || !isValid}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Guardando…
                    </>
                  ) : (
                    "Guardar cambios"
                  )}
                </Button>
                {isDirty && !isSubmitting ? (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancel}
                  >
                    Cancelar
                  </Button>
                ) : null}
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Button variant="outline" onClick={() => navigate("/")}>
        <ArrowLeft />
        Volver
      </Button>
    </div>
  )
}