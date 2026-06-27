describe('Registro', () => {
  beforeEach(() => {
    cy.clearAuth()
  })

  it('muestra el formulario en /register', () => {
    cy.visit('/register')
    cy.contains('Crear cuenta').should('be.visible')
    cy.contains('Empezá a registrar tus finanzas').should('be.visible')
    cy.get('input[autocomplete=given-name]').should('exist')
    cy.get('input[autocomplete=family-name]').should('exist')
    cy.get('input[type=email]').should('exist')
    cy.get('input[autocomplete=new-password]').should('have.length', 2)
    cy.contains('button', 'Crear cuenta').should('be.visible')
  })

  it('rechaza contraseñas que no coinciden', () => {
    cy.visit('/register')
    cy.get('input[autocomplete=given-name]').type('Test')
    cy.get('input[autocomplete=family-name]').type('User')
    cy.get('input[type=email]').type('newuser@test.local')
    cy.get('input[autocomplete=new-password]').eq(0).type('Password1')
    cy.get('input[autocomplete=new-password]').eq(1).type('Distinta1')
    cy.contains('button', 'Crear cuenta').click()
    cy.contains(/no coinciden/i).should('be.visible')
  })

  it('rechaza email inválido en validación cliente', () => {
    cy.visit('/register')
    cy.get('input[autocomplete=given-name]').type('Test')
    cy.get('input[autocomplete=family-name]').type('User')
    cy.get('input[type=email]').type('a@')
    cy.get('input[autocomplete=new-password]').eq(0).type('Password1')
    cy.get('input[autocomplete=new-password]').eq(1).type('Password1')
    cy.contains('button', 'Crear cuenta').click()
    // validación HTML5 nativa: el form no se envía y el input queda :invalid
    cy.url().should('include', '/register')
    cy.get('input[type=email]:invalid').should('exist')
  })

  it('registro exitoso redirige a /', () => {
    const email = `new+${Date.now()}@e2e.local`
    cy.visit('/register')
    cy.get('input[autocomplete=given-name]').type('Nuevo')
    cy.get('input[autocomplete=family-name]').type('Usuario')
    cy.get('input[type=email]').type(email)
    cy.get('input[autocomplete=new-password]').eq(0).type('Password1')
    cy.get('input[autocomplete=new-password]').eq(1).type('Password1')
    cy.contains('button', 'Crear cuenta').click()
    cy.url({ timeout: 10000 }).should('not.include', '/register')
    cy.contains('h1', /Bienvenido/i)
  })

  it('usuario authed no puede acceder a /login (redirige a /)', () => {
    cy.loginAsFixture('primary').then(() => {
      cy.visit('/login')
      cy.url().should('not.include', '/login')
    })
  })
})