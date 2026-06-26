import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  type ReactNode,
} from "react"
import {
  ApiError,
  fetchCurrentUser,
  loginRequest,
  logoutRequest,
  registerRequest,
  setUnauthorizedHandler,
  updateProfile as updateProfileRequest,
} from "@/lib/api"
import { clearTokens, setTokens } from "@/auth/storage"
import type { AuthSession, AuthUser, ProfileInput } from "@/lib/schemas"

type Status = "loading" | "guest" | "authed"

type State = {
  status: Status
  user: AuthUser | null
}

type Action =
  | { type: "BOOT_OK"; user: AuthUser }
  | { type: "BOOT_GUEST" }
  | { type: "LOGIN_OK"; user: AuthUser }
  | { type: "LOGOUT" }

const initialState: State = { status: "loading", user: null }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "BOOT_OK":
    case "LOGIN_OK":
      return { status: "authed", user: action.user }
    case "BOOT_GUEST":
    case "LOGOUT":
      return { status: "guest", user: null }
    default:
      return state
  }
}

export type AuthContextValue = {
  status: Status
  user: AuthUser | null
  login: (email: string, password: string) => Promise<AuthUser>
  register: (input: {
    email: string
    password: string
    first_name: string
    last_name: string
  }) => Promise<AuthSession>
  logout: () => Promise<void>
  refreshUser: () => Promise<AuthUser>
  updateProfile: (input: ProfileInput) => Promise<AuthUser>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const stateRef = useRef(state)
  stateRef.current = state

  const finishAsGuest = useCallback(() => {
    clearTokens()
    dispatch({ type: "BOOT_GUEST" })
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      finishAsGuest()
    })
  }, [finishAsGuest])

  useEffect(() => {
    let cancelled = false
    async function boot() {
      try {
        const user = await fetchCurrentUser()
        if (!cancelled) dispatch({ type: "BOOT_OK", user })
      } catch {
        if (!cancelled) finishAsGuest()
      }
    }
    boot()
    return () => {
      cancelled = true
    }
  }, [finishAsGuest])

  const login = useCallback(async (email: string, password: string) => {
    const session = await loginRequest(email, password)
    setTokens(session.tokens)
    dispatch({ type: "LOGIN_OK", user: session.user })
    return session.user
  }, [])

  const register = useCallback(
    async (input: {
      email: string
      password: string
      first_name: string
      last_name: string
    }) => {
      const session = await registerRequest(input)
      setTokens(session.tokens)
      dispatch({ type: "LOGIN_OK", user: session.user })
      return session
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      const refresh = localStorage.getItem("pf.refresh")
      if (refresh) await logoutRequest(refresh)
    } catch (err) {
      if (!(err instanceof ApiError)) {
        console.error("logout failed", err)
      }
    } finally {
      clearTokens()
      dispatch({ type: "LOGOUT" })
    }
  }, [])

  const refreshUser = useCallback(async () => {
    const user = await fetchCurrentUser()
    dispatch({ type: "LOGIN_OK", user })
    return user
  }, [])

  const updateProfile = useCallback(async (input: ProfileInput) => {
    const user = await updateProfileRequest(input)
    dispatch({ type: "LOGIN_OK", user })
    return user
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      status: state.status,
      user: state.user,
      login,
      register,
      logout,
      refreshUser,
      updateProfile,
    }),
    [
      state.status,
      state.user,
      login,
      register,
      logout,
      refreshUser,
      updateProfile,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
