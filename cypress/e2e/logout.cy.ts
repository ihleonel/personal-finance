describe('Logout', () => {
  beforeEach(() => {
    cy.loginAsFixture('primary')
    cy.visit('/')
  })

  it('el menú de usuario muestra el email y nombre', () => {
    cy.viewport(1280, 720)
    cy.fixture('users').then((users) => {
      cy.contains(users.primary.email)
      cy.contains(users.primary.first_name)
    })
  })

  it('logout desde el UserMenu redirige a /login y limpia la sesión', () => {
    cy.viewport(1280, 720)
    cy.fixture('users').then((users) => {
      const u = users.primary
      const nombreCompleto = `${u.first_name} ${u.last_name}`
      cy.contains('button', new RegExp(nombreCompleto.replace(' ', '\\s*'), 'i')).click()
    })
    cy.get('[role=menuitem]').contains('Cerrar sesión').click()
    cy.url().should('include', '/login')

    cy.visit('/')
    cy.url().should('include', '/login')
    cy.window().then((win) => {
      expect(win.localStorage.getItem('pf.access')).to.be.null
      expect(win.localStorage.getItem('pf.refresh')).to.be.null
    })
  })
})