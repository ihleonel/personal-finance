describe('Rutas protegidas', () => {
  beforeEach(() => {
    cy.clearAuth()
  })

  it('visitar / sin auth redirige a /login', () => {
    cy.visit('/')
    cy.url().should('include', '/login')
  })

  it('visitar /profile sin auth redirige a /login', () => {
    cy.visit('/profile')
    cy.url().should('include', '/login')
  })

  it('visitar una ruta inexistente sin auth redirige a /login', () => {
    cy.visit('/esta-ruta-no-existe')
    cy.url().should('include', '/login')
  })

  it('logueado puede acceder a / y /profile', () => {
    cy.loginAsFixture('primary').then(() => {
      cy.visit('/')
      cy.url().should('eq', Cypress.config().baseUrl + '/')
      cy.contains('h1', /Bienvenido/i)

      cy.visit('/profile')
      cy.url().should('include', '/profile')
      cy.contains('h1', 'Mi perfil')
    })
  })
})