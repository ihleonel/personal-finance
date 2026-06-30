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
  TRANSACTION_KINDS,
  type Account,
  type Category,
  type Transaction,
  type TransactionInput,
  type TransactionUpdateInput,
  transactionSchema,
  transactionUpdateSchema,
} from "@/lib/schemas"
import { createTransaction, updateTransaction } from "@/lib/api"
import { extractApiError } from "@/lib/errors"

type TransactionFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  transaction?: Transaction | null
  accounts: Account[]
  categories: Category[]
  onSaved: (transaction: Transaction) => void
}

function todayISO(): string {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, "0")
  const dd = String(d.getDate()).padStart(2, "0")
  return `${yyyy}-${mm}-${dd}`
}

export function TransactionFormDialog({
  open,
  onOpenChange,
  transaction,
  accounts,
  categories,
  onSaved,
}: TransactionFormDialogProps) {
  const isEdit = transaction != null
  const [submitError, setSubmitError] = useState<string | null>(null)

  const createForm = useForm<TransactionInput>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      account_id: 0,
      kind: "income",
      amount: "",
      date: todayISO(),
      category_id: null,
      description: "",
    },
  })

  const editForm = useForm<TransactionUpdateInput>({
    resolver: zodResolver(transactionUpdateSchema),
    defaultValues: {
      amount: "",
      date: todayISO(),
      description: "",
      category_id: null,
    },
  })

  const isSubmitting = isEdit
    ? editForm.formState.isSubmitting
    : createForm.formState.isSubmitting

  useEffect(() => {
    if (!open) return
    if (isEdit && transaction) {
      editForm.reset({
        amount: transaction.amount,
        date: transaction.date,
        description: transaction.description,
        category_id: transaction.category_id,
      })
    } else {
      createForm.reset({
        account_id: accounts[0]?.id ?? 0,
        kind: "income",
        amount: "",
        date: todayISO(),
        category_id: null,
        description: "",
      })
    }
  }, [open, transaction, isEdit, accounts, createForm, editForm])

  function handleOpenChange(next: boolean) {
    if (!next) setSubmitError(null)
    onOpenChange(next)
  }

  async function onCreate(values: TransactionInput) {
    setSubmitError(null)
    try {
      const saved = await createTransaction(values)
      toast.success("Transacción creada")
      onSaved(saved)
      onOpenChange(false)
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos guardar la transacción")
    }
  }

  async function onEdit(values: TransactionUpdateInput) {
    if (!transaction) return
    setSubmitError(null)
    try {
      const saved = await updateTransaction(transaction.id, values)
      toast.success("Transacción actualizada")
      onSaved(saved)
      onOpenChange(false)
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos guardar la transacción")
    }
  }

  const activeAccounts = accounts.filter((a) => a.is_active)
  const selectedKind = createForm.watch("kind")
  const filteredCategories = categories.filter(
    (c) => c.is_active && c.kind === selectedKind,
  )

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Editar transacción" : "Nueva transacción"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modificá los datos de la transacción."
              : "Registrá un ingreso o egreso en una de tus cuentas."}
          </DialogDescription>
        </DialogHeader>

        {submitError ? (
          <Alert variant="destructive">
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        ) : null}

        {isEdit ? (
          <Form {...editForm}>
            <form
              onSubmit={editForm.handleSubmit(onEdit)}
              className="space-y-4"
              id="transaction-form"
            >
              <FormField
                control={editForm.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monto</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="0.00"
                        disabled={isSubmitting}
                        data-testid="tx-amount-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={editForm.control}
                name="date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fecha</FormLabel>
                    <FormControl>
                      <Input
                        type="date"
                        disabled={isSubmitting}
                        data-testid="tx-date-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={editForm.control}
                name="category_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Categoría</FormLabel>
                    <Select
                      value={field.value == null ? "none" : String(field.value)}
                      onValueChange={(v) =>
                        field.onChange(v === "none" ? null : Number(v))
                      }
                      disabled={isSubmitting}
                    >
                      <FormControl>
                        <SelectTrigger data-testid="tx-category-select">
                          <SelectValue placeholder="Sin categoría" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="none">Sin categoría</SelectItem>
                        {categories
                          .filter((c) => c.is_active && c.kind === transaction.kind)
                          .map((c) => (
                            <SelectItem key={c.id} value={String(c.id)}>
                              {c.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={editForm.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Descripción</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Opcional"
                        disabled={isSubmitting}
                        data-testid="tx-description-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </form>
          </Form>
        ) : (
          <Form {...createForm}>
            <form
              onSubmit={createForm.handleSubmit(onCreate)}
              className="space-y-4"
              id="transaction-form"
            >
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={createForm.control}
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
                          <SelectTrigger data-testid="tx-kind-select">
                            <SelectValue placeholder="Seleccioná un tipo" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {TRANSACTION_KINDS.map((k) => (
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

                <FormField
                  control={createForm.control}
                  name="account_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Cuenta</FormLabel>
                      <Select
                        value={field.value ? String(field.value) : ""}
                        onValueChange={(v) => field.onChange(Number(v))}
                        disabled={isSubmitting}
                      >
                        <FormControl>
                          <SelectTrigger data-testid="tx-account-select">
                            <SelectValue placeholder="Seleccioná una cuenta" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {activeAccounts.map((a) => (
                            <SelectItem key={a.id} value={String(a.id)}>
                              {a.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={createForm.control}
                  name="amount"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Monto</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="0.00"
                          disabled={isSubmitting}
                          data-testid="tx-amount-input"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={createForm.control}
                  name="date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Fecha</FormLabel>
                      <FormControl>
                        <Input
                          type="date"
                          disabled={isSubmitting}
                          data-testid="tx-date-input"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={createForm.control}
                name="category_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Categoría</FormLabel>
                    <Select
                      value={field.value == null ? "none" : String(field.value)}
                      onValueChange={(v) =>
                        field.onChange(v === "none" ? null : Number(v))
                      }
                      disabled={isSubmitting}
                    >
                      <FormControl>
                        <SelectTrigger data-testid="tx-category-select">
                          <SelectValue placeholder="Sin categoría" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="none">Sin categoría</SelectItem>
                        {filteredCategories.map((c) => (
                          <SelectItem key={c.id} value={String(c.id)}>
                            {c.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={createForm.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Descripción</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Opcional"
                        disabled={isSubmitting}
                        data-testid="tx-description-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </form>
          </Form>
        )}

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
            form="transaction-form"
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
              "Crear transacción"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}