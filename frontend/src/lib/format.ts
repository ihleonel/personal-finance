export function getInitials(firstName?: string, lastName?: string): string {
  const f = firstName?.trim().charAt(0) ?? ""
  const l = lastName?.trim().charAt(0) ?? ""
  const result = (f + l).toUpperCase()
  return result || "?"
}

export function formatBalance(
  amount: string | number,
  currency: string,
): string {
  const value = typeof amount === "string" ? Number(amount) : amount
  if (!Number.isFinite(value)) return String(amount)
  try {
    return new Intl.NumberFormat("es-AR", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(value)
  } catch {
    return `${currency} ${value.toFixed(2)}`
  }
}