import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
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
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  RULE_MATCH_TYPES,
  categoryRuleFormSchema,
  type CategorizationRule,
  type Category,
  type CategoryRuleFormInput,
} from "@/lib/schemas"
import { createCategorizationRule, updateCategorizationRule } from "@/lib/api"
import { extractApiError } from "@/lib/errors"

type CategoryRuleFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: Category | null
  rule?: CategorizationRule | null
  onSaved: (rule: CategorizationRule) => void
}

export function CategoryRuleFormDialog({
  open,
  onOpenChange,
  category,
  rule,
  onSaved,
}: CategoryRuleFormDialogProps) {
  const isEdit = rule != null
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<CategoryRuleFormInput>({
    resolver: zodResolver(categoryRuleFormSchema),
    defaultValues: {
      pattern: "",
      match_type: "contains",
      priority: 0,
    },
  })

  useEffect(() => {
    if (!open) return
    if (isEdit && rule) {
      form.reset({
        pattern: rule.pattern,
        match_type: rule.match_type as CategoryRuleFormInput["match_type"],
        priority: rule.priority,
      })
    } else {
      form.reset({
        pattern: "",
        match_type: "contains",
        priority: 0,
      })
    }
  }, [open, rule, isEdit, form])

  function handleOpenChange(next: boolean) {
    if (!next) setSubmitError(null)
    onOpenChange(next)
  }

  const isSubmitting = form.formState.isSubmitting

  async function onSubmit(values: CategoryRuleFormInput) {
    setSubmitError(null)
    if (!category) return
    try {
      const saved = isEdit
        ? await updateCategorizationRule(rule!.id, values)
        : await createCategorizationRule({
            ...values,
            category_id: category.id,
            kind: category.kind as "income" | "expense",
          })
      toast.success(isEdit ? "Regla actualizada" : "Regla creada")
      onSaved(saved)
      onOpenChange(false)
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos guardar la regla")
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Editar regla" : "Nueva regla de categorización"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modificá los datos de la regla."
              : `Creá una regla para asignar ${category?.name ?? "esta categoría"} automáticamente según la descripción de la transacción.`}
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
            id="category-rule-form"
          >
            <FormField
              control={form.control}
              name="pattern"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Patrón</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ej. uber, coto, mercado pago"
                      disabled={isSubmitting}
                      data-testid="rule-pattern-input"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="match_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Coincidencia</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={isSubmitting}
                    >
                      <FormControl>
                        <SelectTrigger data-testid="rule-match-type-select">
                          <SelectValue placeholder="Seleccioná un tipo" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {RULE_MATCH_TYPES.map((m) => (
                          <SelectItem key={m.value} value={m.value}>
                            {m.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="priority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Prioridad</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        step={1}
                        disabled={isSubmitting}
                        data-testid="rule-priority-input"
                        {...field}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value === "" ? 0 : Number(e.target.value),
                          )
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
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
            form="category-rule-form"
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
              "Crear regla"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}