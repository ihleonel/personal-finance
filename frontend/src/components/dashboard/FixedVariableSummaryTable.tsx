import { TrendingDown } from "lucide-react"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatAmount } from "@/lib/format"
import type { CategorySummary } from "@/lib/schemas"

type FixedVariableSummaryTableProps = {
  fixed: CategorySummary
  variable: CategorySummary
}

function sumValues(values: Array<string | undefined>): number {
  return values.reduce<number>((acc, v) => {
    if (v === undefined) return acc
    const n = Number(v)
    return Number.isFinite(n) ? acc + n : acc
  }, 0)
}

export function FixedVariableSummaryTable({
  fixed,
  variable,
}: FixedVariableSummaryTableProps) {
  const cols = fixed.columns
  const isEmpty = cols.length === 0

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky left-0 bg-background">Categoría</TableHead>
            {cols.map((c) => (
              <TableHead key={c.key} className="text-right whitespace-nowrap">
                {c.label}
                {c.is_partial ? (
                  <span className="ml-1 text-xs font-normal text-muted-foreground">
                    (parcial)
                  </span>
                ) : null}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isEmpty ? (
            <TableRow>
              <TableCell
                colSpan={cols.length + 1}
                className="text-center text-muted-foreground py-6"
              >
                No hay datos para los filtros seleccionados.
              </TableCell>
            </TableRow>
          ) : (
            <>
              <TableRow data-testid="fv-fixed-row">
                <TableCell className="sticky left-0 bg-background">
                  <div className="flex items-center gap-2">
                    <TrendingDown className="h-3.5 w-3.5 text-destructive" />
                    <span>Gastos fijos</span>
                  </div>
                </TableCell>
                {fixed.totals.amounts.map((amt, i) => {
                  const value = Number(amt)
                  const display =
                    value === 0 ? "—" : formatAmount(Math.abs(value))
                  const color =
                    value === 0
                      ? "text-muted-foreground"
                      : "text-destructive"
                  return (
                    <TableCell
                      key={`fixed-${cols[i].key}`}
                      className={`text-right tabular-nums ${color}`}
                    >
                      {display}
                    </TableCell>
                  )
                })}
              </TableRow>

              <TableRow data-testid="fv-variable-row">
                <TableCell className="sticky left-0 bg-background">
                  <div className="flex items-center gap-2">
                    <TrendingDown className="h-3.5 w-3.5 text-destructive" />
                    <span>Gastos variables</span>
                  </div>
                </TableCell>
                {variable.totals.amounts.map((amt, i) => {
                  const value = Number(amt)
                  const display =
                    value === 0 ? "—" : formatAmount(Math.abs(value))
                  const color =
                    value === 0
                      ? "text-muted-foreground"
                      : "text-destructive"
                  return (
                    <TableCell
                      key={`variable-${cols[i].key}`}
                      className={`text-right tabular-nums ${color}`}
                    >
                      {display}
                    </TableCell>
                  )
                })}
              </TableRow>

              <TableRow data-testid="fv-totals-row" className="border-t-2">
                <TableCell className="sticky left-0 bg-background font-semibold">
                  Total
                </TableCell>
                {cols.map((c, i) => {
                  const total = sumValues([
                    fixed.totals.amounts[i],
                    variable.totals.amounts[i],
                  ])
                  const display = total === 0 ? "—" : formatAmount(total)
                  const color =
                    total === 0
                      ? "text-muted-foreground"
                      : "text-destructive"
                  return (
                    <TableCell
                      key={`totals-${c.key}`}
                      className={`text-right tabular-nums font-semibold ${color}`}
                    >
                      {display}
                    </TableCell>
                  )
                })}
              </TableRow>
            </>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
