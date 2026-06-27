/// <reference types="cypress" />

type AuthTokens = { access: string; refresh: string }
type AuthUser = {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
}

declare global {
  namespace Cypress {
    interface Chainable {
      loginAs(email: string, password: string): Chainable<{ user: AuthUser; tokens: AuthTokens }>
      loginAsFixture(name?: string): Chainable<{ user: AuthUser; tokens: AuthTokens }>
      setAuthTokens(tokens: AuthTokens): Chainable<void>
      clearAuth(): Chainable<void>
    }
  }
}

Cypress.Commands.add('setAuthTokens', (tokens: AuthTokens) => {
  window.localStorage.setItem('pf.access', tokens.access)
  window.localStorage.setItem('pf.refresh', tokens.refresh)
})

Cypress.Commands.add('clearAuth', () => {
  window.localStorage.removeItem('pf.access')
  window.localStorage.removeItem('pf.refresh')
})

Cypress.Commands.add('loginAs', (email: string, password: string) => {
  return cy
    .request({
      method: 'POST',
      url: '/api/auth/login/',
      body: { email, password },
    })
    .then((res) => {
      const body = res.body as { user: AuthUser; tokens: AuthTokens }
      cy.setAuthTokens(body.tokens).then(() => body)
    })
})

Cypress.Commands.add('loginAsFixture', (name: string = 'primary') => {
  return cy.fixture('users').then((users: Record<string, { email: string; password: string }>) => {
    const u = users[name]
    if (!u) throw new Error(`Fixture user "${name}" not found`)
    return cy.loginAs(u.email, u.password)
  })
})

export {}