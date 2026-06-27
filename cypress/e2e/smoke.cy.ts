describe('Smoke', () => {
  beforeEach(() => {
    cy.clearAuth()
  })

  it('visitar la raíz sin auth redirige a /login', () => {
    cy.visit('/')
    cy.url().should('include', '/login')
    cy.contains('Iniciar sesión').should('be.visible')
    cy.contains('Ingresá tu email').should('be.visible')
  })
})