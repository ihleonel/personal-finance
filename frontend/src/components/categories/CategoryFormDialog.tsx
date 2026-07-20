import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  CATEGORY_KINDS,
  categorySchema,
  type Category,
  type CategoryInput,
} from "@/lib/schemas"
import { createCategory, updateCategory } from "@/lib/api"
import { extractApiError } from "@/lib/errors"

type CategoryFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  category?: Category | null
  onSaved: (category: Category) => void
}

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
  onSaved,
}: CategoryFormDialogProps) {
  const isEdit = category != null
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<CategoryInput>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: "",
      kind: "expense",
      include_in_summaries: true,
    },
  })

  useEffect(() => {
    if (!open) return
    const initial = category
      ? {
          name: category.name,
          kind: category.kind as CategoryInput["kind"],
          include_in_summaries: category.include_in_summaries,
        }
      : {
          name: "",
          kind: "expense" as CategoryInput["kind"],
          include_in_summaries: true,
        }
    form.reset(initial)
  }, [open, category, form])

  function handleOpenChange(next: boolean) {
    if (!next) setSubmitError(null)
    onOpenChange(next)
  }

  const isSubmitting = form.formState.isSubmitting

  async function onSubmit(values: CategoryInput) {
    setSubmitError(null)
    try {
      const saved = isEdit
        ? await updateCategory(category!.id, values)
        : await createCategory(values)
      toast.success(isEdit ? "Categoría actualizada" : "Categoría creada")
      onSaved(saved)
      onOpenChange(false)
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos guardar la categoría")
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Editar categoría" : "Nueva categoría"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modificá los datos de la categoría."
              : "Creá una categoría para clasificar tus ingresos o egresos."}
          </DialogDescription>
        </DialogHeader>

        {submitError ? (
          <Alert variant="destructive">
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        ) : null}

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-4"
            id="category-form"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nombre</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ej. Sueldo, Comida, Alquiler"
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
              name="kind"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={isSubmitting}
                  >
                    <FormControl>
                      <SelectTrigger data-testid="category-kind-select">
                        <SelectValue placeholder="Seleccioná un tipo" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {CATEGORY_KINDS.map((k) => (
                        <SelectItem key={k.value} value={k.value}>
                          {k.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Separator className="my-2" />

            <FormField
              control={form.control}
              name="include_in_summaries"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel className="cursor-pointer">
                      Incluir en resúmenes
                    </FormLabel>
                    <p className="text-sm text-muted-foreground">
                      Si desactivás esta opción, los movimientos con esta
                      categoría no se sumarán a los totales de ingresos y egresos
                      en el dashboard. Usalo para categorías patrimoniales como
                      ahorro o transferencias.
                    </p>
                    <FormMessage />
                  </div>
                </FormItem>
              )}
            />
          </form>
        </Form>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="category-form"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" />
                Guardando…
              </>
            ) : isEdit ? (
              "Guardar cambios"
            ) : (
              "Crear categoría"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}