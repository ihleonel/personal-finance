import { ApiError } from "@/lib/api"

function firstString(value: unknown): string | null {
  if (typeof value === "string") return value
  if (Array.isArray(value)) {
    const first = value.find((v) => typeof v === "string")
    return typeof first === "string" ? first : null
  }
  return null
}

/**
 * Extrae un mensaje de error amigable desde un error de la API.
 *
 * Soporta los formatos de respuesta usados por el backend:
 * - `{ detail: "mensaje" }` (errores 404, 403, etc. de DRF)
 * - `{ field: ["mensaje", ...] }` (errores de validación por campo de DRF)
 * - `"mensaje"` (string directo)
 */
export function extractApiError(err: unknown): string | null {
  if (!(err instanceof ApiError)) return null

  const data = err.data
  if (typeof data === "string") return data

  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>

    const detail = obj.detail
    if (typeof detail === "string") return detail
    if (Array.isArray(detail)) {
      const first = firstString(detail)
      if (first) return first
    }

    const values = Object.values(obj)
    for (const value of values) {
      const message = firstString(value)
      if (message) return message
    }
  }

  return err.message
}