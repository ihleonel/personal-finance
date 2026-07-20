import { useState } from "react"
import { CheckCircle2, Loader2, Upload } from "lucide-react"
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
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { type Account, type ImportTransactionResult } from "@/lib/schemas"
import { importTransactions } from "@/lib/api"
import { extractApiError } from "@/lib/errors"

type ImportTransactionsDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  accounts: Account[]
  onImported: (result: ImportTransactionResult) => void
}

const MAX_SIZE_BYTES = 2 * 1024 * 1024

export function ImportTransactionsDialog({
  open,
  onOpenChange,
  accounts,
  onImported,
}: ImportTransactionsDialogProps) {
  const activeAccounts = accounts.filter((a) => a.is_active)
  const [accountId, setAccountId] = useState<number>(activeAccounts[0]?.id ?? 0)
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [result, setResult] = useState<ImportTransactionResult | null>(null)
  const [prevOpen, setPrevOpen] = useState(open)

  if (open !== prevOpen) {
    setPrevOpen(open)
    if (open) {
      setAccountId(activeAccounts[0]?.id ?? 0)
      setFile(null)
      setSubmitting(false)
      setSubmitError(null)
      setResult(null)
    }
  }

  function handleOpenChange(next: boolean) {
    if (!next) setSubmitError(null)
    onOpenChange(next)
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSubmitError(null)
    const f = e.target.files?.[0] ?? null
    setFile(f)
  }

  async function handleSubmit() {
    setSubmitError(null)
    if (!accountId) {
      setSubmitError("Seleccioná una cuenta.")
      return
    }
    if (!file) {
      setSubmitError("Seleccioná un archivo CSV.")
      return
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setSubmitError("El archivo debe tener extensión .csv.")
      return
    }
    if (file.size > MAX_SIZE_BYTES) {
      setSubmitError("El archivo no puede pesar más de 2 MB.")
      return
    }

    setSubmitting(true)
    try {
      const res = await importTransactions(file, accountId)
      setResult(res)
      if (res.summary.errors > 0) {
        toast.warning(
          `Se importaron ${res.summary.created} transacciones con ${res.summary.errors} errores`,
        )
      } else {
        toast.success(`Se importaron ${res.summary.created} transacciones`)
      }
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos importar el archivo")
    } finally {
      setSubmitting(false)
    }
  }

  function handleClose() {
    if (result) onImported(result)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Importar transacciones</DialogTitle>
          <DialogDescription>
            Subí un reporte CSV de tu banco o billetera virtual. El formato se
            detecta automáticamente.
          </DialogDescription>
        </DialogHeader>

        {submitError ? (
          <Alert variant="destructive">
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        ) : null}

        {result ? (
          <div className="space-y-4" data-testid="import-result-panel">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <SummaryStat
                label="Creadas"
                value={result.summary.created}
                tone="positive"
                testId="import-summary-created"
              />
              <SummaryStat
                label="Duplicadas"
                value={result.summary.skipped}
                tone="muted"
                testId="import-summary-skipped"
              />
              <SummaryStat
                label="Con errores"
                value={result.summary.errors}
                tone={result.summary.errors > 0 ? "destructive" : "muted"}
                testId="import-summary-errors"
              />
              <SummaryStat
                label="Total"
                value={result.summary.total}
                tone="muted"
                testId="import-summary-total"
              />
            </div>

            {result.errors.length > 0 ? (
              <div className="space-y-1.5">
                <p className="text-sm font-medium text-destructive">
                  Filas con errores
                </p>
                <div
                  className="max-h-60 overflow-y-auto rounded-lg border border-border"
                  data-testid="import-errors-list"
                >
                  <ul className="divide-y divide-border">
                    {result.errors.map((e, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 px-3 py-2 text-sm"
                      >
                        <span className="shrink-0 font-medium text-muted-foreground">
                          Fila {e.row_number}
                        </span>
                        <span className="text-destructive">{e.message}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}

            {result.summary.skipped > 0 ? (
              <p className="text-sm text-muted-foreground">
                {result.summary.skipped} transacció
                {result.summary.skipped === 1 ? "n" : "es"} duplicada
                {result.summary.skipped === 1 ? "" : "s"} no se importaron de
                nuevo.
              </p>
            ) : null}

          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Cuenta</label>
              <Select
                value={accountId ? String(accountId) : ""}
                onValueChange={(v) => setAccountId(Number(v))}
                disabled={submitting}
              >
                <SelectTrigger data-testid="import-account-select">
                  <SelectValue placeholder="Seleccioná una cuenta" />
                </SelectTrigger>
                <SelectContent>
                  {activeAccounts.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Archivo CSV</label>
              <Input
                type="file"
                accept=".csv,text/csv"
                disabled={submitting}
                data-testid="import-file-input"
                onChange={handleFileChange}
              />
              {file ? (
                <p className="text-xs text-muted-foreground">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </p>
              ) : null}
            </div>
          </div>
        )}

        <DialogFooter>
          {result ? (
            <Button onClick={handleClose} data-testid="import-close">
              Cerrar
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={submitting}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                data-testid="import-submit"
              >
                {submitting ? (
                  <>
                    <Loader2 className="animate-spin" />
                    Importando…
                  </>
                ) : (
                  <>
                    <Upload />
                    Importar
                  </>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function SummaryStat({
  label,
  value,
  tone,
  testId,
}: {
  label: string
  value: number
  tone: "positive" | "muted" | "destructive"
  testId?: string
}) {
  const color =
    tone === "positive"
      ? "text-secondary-foreground"
      : tone === "destructive"
        ? "text-destructive"
        : "text-muted-foreground"
  return (
    <div
      className="rounded-lg border border-border bg-muted/30 px-3 py-2"
      data-testid={testId}
    >
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`flex items-center gap-1 text-lg font-semibold ${color}`}>
        {tone === "positive" && value > 0 ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : null}
        {value}
      </p>
    </div>
  )
}