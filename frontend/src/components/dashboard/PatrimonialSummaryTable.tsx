import { TrendingDown, TrendingUp } from "lucide-react"

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

type PatrimonialSummaryTableProps = {
  summary: CategorySummary
}

export function PatrimonialSummaryTable({ summary }: PatrimonialSummaryTableProps) {
  const cols = summary.columns
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky left-0 bg-background">
              Categoría
            </TableHead>
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
          {summary.rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={cols.length + 1}
                className="text-center text-muted-foreground py-6"
              >
                No tenés categorías patrimoniales todavía.
              </TableCell>
            </TableRow>
          ) : (
            summary.rows.map((row) => {
              const isIncome = row.kind === "income"
              const muted = row.is_uncategorized || !row.is_active
              return (
                <TableRow
                  key={`${row.kind}-${row.category_id ?? "none"}`}
                >
                  <TableCell className="sticky left-0 bg-background">
                    <div className="flex items-center gap-2">
                      {isIncome ? (
                        <TrendingUp className="h-3.5 w-3.5 text-secondary-foreground" />
                      ) : (
                        <TrendingDown className="h-3.5 w-3.5 text-destructive" />
                      )}
                      <span className={muted ? "italic text-muted-foreground" : ""}>
                        {row.name}
                      </span>
                      {!row.is_active && !row.is_uncategorized ? (
                        <span className="text-xs text-muted-foreground">(inactiva)</span>
                      ) : null}
                    </div>
                  </TableCell>
                  {row.amounts.map((amt, i) => {
                    const value = Number(amt)
                    const display = value === 0 ? "—" : formatAmount(amt)
                    const color =
                      value === 0
                        ? "text-muted-foreground"
                        : isIncome
                          ? "text-secondary-foreground"
                          : "text-destructive"
                    return (
                      <TableCell
                        key={`${row.kind}-${row.category_id ?? "none"}-${cols[i].key}`}
                        className={`text-right tabular-nums ${color}`}
                      >
                        {display}
                      </TableCell>
                    )
                  })}
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>
    </div>
  )
}
