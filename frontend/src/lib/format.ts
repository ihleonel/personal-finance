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

export function formatAmount(amount: string | number): string {
  const value = typeof amount === "string" ? Number(amount) : amount
  if (!Number.isFinite(value)) return String(amount)
  return new Intl.NumberFormat("es-AR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number)
  const value = new Date(y, m - 1, d)
  if (Number.isNaN(value.getTime())) return iso
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(value)
}