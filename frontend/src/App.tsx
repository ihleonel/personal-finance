import { BrowserRouter } from "react-router-dom"
import { AuthProvider } from "@/auth/AuthContext"
import { Toaster } from "@/components/ui/sonner"
import { AppRoutes } from "@/routes"

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster richColors position="top-right" closeButton />
      </BrowserRouter>
    </AuthProvider>
  )
}
