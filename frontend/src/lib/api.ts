import type { Account, AccountInput, AuthSession, AuthTokens, BulkAssignCategoryInput, BulkAssignCategoryResult, Category, CategoryInput, CategorySummary, CategorizationRule, CategorizationRuleInput, CategorizationRuleUpdateInput, ImportTransactionResult, IncomeExpenseSummary, PaginatedResponse, ProfileInput, ReportFilters, SuggestCategoryResult, Transaction, TransactionFilters, TransactionInput, TransactionUpdateInput } from "@/lib/schemas"
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/auth/storage"

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(status: number, data: unknown, message?: string) {
    super(message ?? `Request failed with status ${status}`)
    this.name = "ApiError"
    this.status = status
    this.data = data
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: unknown
  headers?: Record<string, string>
  skipAuth?: boolean
}

const AUTH_FREE_PATHS = new Set(["/auth/login/", "/auth/register/", "/auth/refresh/"])

let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

async function refreshTokens(): Promise<AuthTokens | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    const res = await fetch("/api/auth/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { access: string; refresh?: string }
    const next: AuthTokens = {
      access: data.access,
      refresh: data.refresh ?? refresh,
    }
    setTokens(next)
    return next
  } catch {
    return null
  }
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const isFormData = opts.body instanceof FormData
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(opts.body !== undefined && !isFormData ? { "Content-Type": "application/json" } : {}),
    ...opts.headers,
  }

  if (!opts.skipAuth && !AUTH_FREE_PATHS.has(path)) {
    const token = getAccessToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers,
  }
  if (opts.body !== undefined) {
    init.body = isFormData ? (opts.body as FormData) : JSON.stringify(opts.body)
  }

  const res = await fetch(`/api${path}`, init)

  if (
    res.status === 401 &&
    !opts.skipAuth &&
    !AUTH_FREE_PATHS.has(path) &&
    getRefreshToken()
  ) {
    const refreshed = await refreshTokens()
    if (refreshed) {
      return request<T>(path, opts)
    }
    clearTokens()
    onUnauthorized?.()
  }

  if (!res.ok) {
    const data: unknown = await res.json().catch(() => null)
    throw new ApiError(res.status, data)
  }

  if (res.status === 204) {
    return undefined as T
  }
  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
}

export async function loginRequest(email: string, password: string): Promise<AuthSession> {
  return api.post<AuthSession>("/auth/login/", { email, password })
}

export async function registerRequest(input: {
  email: string
  password: string
  first_name: string
  last_name: string
}): Promise<AuthSession> {
  return api.post<AuthSession>("/auth/register/", input)
}

export async function logoutRequest(refresh: string): Promise<void> {
  await api.post<void>("/auth/logout/", { refresh })
}

export async function fetchCurrentUser(): Promise<AuthSession["user"]> {
  return api.get<AuthSession["user"]>("/auth/me/")
}

export async function fetchProfile(): Promise<AuthSession["user"]> {
  return api.get<AuthSession["user"]>("/auth/profile/")
}

export async function updateProfile(
  input: ProfileInput,
): Promise<AuthSession["user"]> {
  return api.patch<AuthSession["user"]>("/auth/profile/", input)
}

export async function changePasswordRequest(input: {
  current_password: string
  new_password: string
}): Promise<{ detail: string }> {
  return api.post<{ detail: string }>("/auth/change-password/", input)
}

export async function fetchAccounts(): Promise<Account[]> {
  return api.get<Account[]>("/accounts/")
}

export async function createAccount(input: AccountInput): Promise<Account> {
  return api.post<Account>("/accounts/", input)
}

export async function updateAccount(
  id: number,
  input: Partial<AccountInput>,
): Promise<Account> {
  return api.patch<Account>(`/accounts/${id}/`, input)
}

export async function deactivateAccount(id: number): Promise<Account> {
  return api.post<Account>(`/accounts/${id}/deactivate/`, {})
}

export async function activateAccount(id: number): Promise<Account> {
  return api.post<Account>(`/accounts/${id}/activate/`, {})
}

export async function fetchCategories(): Promise<Category[]> {
  return api.get<Category[]>("/categories/")
}

export async function createCategory(input: CategoryInput): Promise<Category> {
  return api.post<Category>("/categories/", input)
}

export async function updateCategory(
  id: number,
  input: Partial<CategoryInput>,
): Promise<Category> {
  const body: Record<string, unknown> = { ...input }
  if (input.include_in_summaries !== undefined) {
    body.include_in_summaries = input.include_in_summaries
  }
  return api.patch<Category>(`/categories/${id}/`, body)
}

export async function deactivateCategory(id: number): Promise<Category> {
  return api.post<Category>(`/categories/${id}/deactivate/`, {})
}

export async function activateCategory(id: number): Promise<Category> {
  return api.post<Category>(`/categories/${id}/activate/`, {})
}

export async function fetchCategorizationRules(): Promise<CategorizationRule[]> {
  return api.get<CategorizationRule[]>("/categorization-rules/")
}

export async function createCategorizationRule(
  input: CategorizationRuleInput,
): Promise<CategorizationRule> {
  return api.post<CategorizationRule>("/categorization-rules/", input)
}

export async function updateCategorizationRule(
  id: number,
  input: CategorizationRuleUpdateInput,
): Promise<CategorizationRule> {
  return api.patch<CategorizationRule>(`/categorization-rules/${id}/`, input)
}

export async function deleteCategorizationRule(id: number): Promise<void> {
  await api.del<void>(`/categorization-rules/${id}/`)
}

export async function deactivateCategorizationRule(
  id: number,
): Promise<CategorizationRule> {
  return api.post<CategorizationRule>(`/categorization-rules/${id}/deactivate/`, {})
}

export async function activateCategorizationRule(
  id: number,
): Promise<CategorizationRule> {
  return api.post<CategorizationRule>(`/categorization-rules/${id}/activate/`, {})
}

export async function suggestCategory(
  description: string,
): Promise<SuggestCategoryResult> {
  return api.post<SuggestCategoryResult>("/categorization-rules/suggest-category/", {
    description,
  })
}

function buildQueryString(filters: TransactionFilters, page?: number): string {
  const params = new URLSearchParams()
  if (filters.account_id != null) params.set("account_id", String(filters.account_id))
  if (filters.kind) params.set("kind", filters.kind)
  if (filters.category_id_isnull) params.set("category_id_isnull", "true")
  if (filters.category_id != null) params.set("category_id", String(filters.category_id))
  if (filters.date_from) params.set("date_from", filters.date_from)
  if (filters.date_to) params.set("date_to", filters.date_to)
  if (filters.description) params.set("description", filters.description)
  if (page != null && page > 1) params.set("page", String(page))
  const qs = params.toString()
  return qs ? `?${qs}` : ""
}

export async function fetchTransactions(
  filters?: TransactionFilters,
  page?: number,
): Promise<PaginatedResponse<Transaction>> {
  return api.get<PaginatedResponse<Transaction>>(
    `/transactions/${buildQueryString(filters ?? {}, page)}`,
  )
}

export async function createTransaction(
  input: TransactionInput,
): Promise<Transaction> {
  return api.post<Transaction>("/transactions/", input)
}

export async function updateTransaction(
  id: number,
  input: TransactionUpdateInput,
): Promise<Transaction> {
  return api.patch<Transaction>(`/transactions/${id}/`, input)
}

export async function deleteTransaction(id: number): Promise<void> {
  await api.del<void>(`/transactions/${id}/`)
}

export async function importTransactions(
  file: File,
  accountId: number,
): Promise<ImportTransactionResult> {
  const form = new FormData()
  form.append("file", file)
  form.append("account_id", String(accountId))
  return request<ImportTransactionResult>("/transactions/import/", {
    method: "POST",
    body: form,
  })
}

export async function bulkAssignCategory(
  input: BulkAssignCategoryInput,
): Promise<BulkAssignCategoryResult> {
  return api.post<BulkAssignCategoryResult>(
    "/transactions/bulk-assign-category/",
    input,
  )
}

export async function fetchIncomeExpenseSummary(
  filters: ReportFilters,
): Promise<IncomeExpenseSummary> {
  const params = new URLSearchParams()
  params.set("period", filters.period)
  params.set("periods_count", String(filters.periods_count))
  if (filters.account_id != null) params.set("account_id", String(filters.account_id))
  const qs = params.toString()
  return api.get<IncomeExpenseSummary>(`/reports/income-expense/${qs ? `?${qs}` : ""}`)
}

export async function fetchCategorySummary(
  filters: ReportFilters,
): Promise<CategorySummary> {
  const params = new URLSearchParams()
  params.set("period", filters.period)
  params.set("periods_count", String(filters.periods_count))
  if (filters.account_id != null) params.set("account_id", String(filters.account_id))
  const qs = params.toString()
  return api.get<CategorySummary>(`/reports/category-summary/${qs ? `?${qs}` : ""}`)
}
