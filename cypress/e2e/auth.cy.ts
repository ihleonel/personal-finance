describe('Login', () => {
  beforeEach(() => {
    cy.clearAuth()
  })

  it('muestra el formulario en /login', () => {
    cy.visit('/login')
    cy.contains('Iniciar sesión').should('be.visible')
    cy.contains('Ingresá tu email').should('be.visible')
    cy.get('input[type=email]').should('exist')
    cy.get('input[type=password]').should('exist')
    cy.contains('button', 'Iniciar sesión').should('be.visible')
  })

  it('rechaza credenciales inválidas mostrando mensaje de error', () => {
    cy.visit('/login')
    cy.get('input[type=email]').type('noexiste@test.local')
    cy.get('input[type=password]').type('wrongpass1')
    cy.contains('button', 'Iniciar sesión').click()
    cy.get('[role=alert]', { timeout: 10000 }).should('be.visible')
    cy.contains('[role=alert]', /credenciales inválidas/i).should('be.visible')
    cy.url().should('include', '/login')
  })

  it('muestra error de validación si el email no es válido', () => {
    cy.visit('/login')
    cy.get('input[type=email]').type('a@')
    cy.get('input[type=password]').type('algo12345')
    cy.contains('button', 'Iniciar sesión').click()
    // validación HTML5 nativa: el form no se envía y el input queda :invalid
    cy.url().should('include', '/login')
    cy.get('input[type=email]:invalid').should('exist')
  })

  it('login con credenciales válidas redirige a /', () => {
    cy.loginAsFixture('primary').then(() => {
      cy.visit('/')
      cy.url().should('not.include', '/login')
      cy.contains('h1', /Dashboard/i)
    })
  })
})