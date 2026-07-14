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
  type Account,
  type TransferInput,
  type TransferOutput,
  transferSchema,
} from "@/lib/schemas"
import { createTransfer } from "@/lib/api"
import { extractApiError } from "@/lib/errors"

type TransferFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  accounts: Account[]
  onSaved: (transfer: TransferOutput) => void
}

function todayISO(): string {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, "0")
  const dd = String(d.getDate()).padStart(2, "0")
  return `${yyyy}-${mm}-${dd}`
}

export function TransferFormDialog({
  open,
  onOpenChange,
  accounts,
  onSaved,
}: TransferFormDialogProps) {
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<TransferInput>({
    resolver: zodResolver(transferSchema),
    defaultValues: {
      source_account_id: 0,
      destination_account_id: 0,
      amount: "",
      date: todayISO(),
      description: "",
    },
  })

  const isSubmitting = form.formState.isSubmitting

  useEffect(() => {
    if (!open) return
    form.reset({
      source_account_id: accounts[0]?.id ?? 0,
      destination_account_id: accounts[1]?.id ?? accounts[0]?.id ?? 0,
      amount: "",
      date: todayISO(),
      description: "",
    })
  }, [open, accounts, form])

  function handleOpenChange(next: boolean) {
    if (!next) setSubmitError(null)
    onOpenChange(next)
  }

  async function onSubmit(values: TransferInput) {
    setSubmitError(null)
    try {
      const saved = await createTransfer(values)
      toast.success("Transferencia creada")
      onSaved(saved)
      onOpenChange(false)
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos crear la transferencia")
    }
  }

  const activeAccounts = accounts.filter((a) => a.is_active)

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nueva transferencia</DialogTitle>
          <DialogDescription>
            Mové dinero entre dos de tus cuentas.
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
            id="transfer-form"
          >
            <FormField
              control={form.control}
              name="source_account_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Cuenta de origen</FormLabel>
                  <Select
                    value={field.value ? String(field.value) : ""}
                    onValueChange={(v) => field.onChange(Number(v))}
                    disabled={isSubmitting}
                  >
                    <FormControl>
                      <SelectTrigger data-testid="transfer-source-select">
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

            <FormField
              control={form.control}
              name="destination_account_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Cuenta de destino</FormLabel>
                  <Select
                    value={field.value ? String(field.value) : ""}
                    onValueChange={(v) => field.onChange(Number(v))}
                    disabled={isSubmitting}
                  >
                    <FormControl>
                      <SelectTrigger data-testid="transfer-destination-select">
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

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monto</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="0.00"
                        disabled={isSubmitting}
                        data-testid="transfer-amount-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fecha</FormLabel>
                    <FormControl>
                      <Input
                        type="date"
                        disabled={isSubmitting}
                        data-testid="transfer-date-input"
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
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Descripción</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Opcional"
                      disabled={isSubmitting}
                      data-testid="transfer-description-input"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
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
            form="transfer-form"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" />
                Guardando…
              </>
            ) : (
              "Crear transferencia"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}