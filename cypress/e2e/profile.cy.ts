describe('Perfil', () => {
  const ORIGINAL = { first_name: 'Cy', last_name: 'Press' }

  beforeEach(() => {
    cy.loginAsFixture('primary')
    // restaurar estado del perfil antes de cada test
    cy.window().then((win) => {
      const access = win.localStorage.getItem('pf.access')
      if (access) {
        cy.request({
          method: 'PATCH',
          url: '/api/auth/profile/',
          body: ORIGINAL,
          headers: { Authorization: `Bearer ${access}` },
        })
      }
    })
    cy.visit('/profile')
  })

  after(() => {
    // restaurar estado al final de toda la suite
    cy.request('POST', '/api/auth/login/', {
      email: 'cypress+e2e@personal-finance.local',
      password: 'Cypress12345',
    }).then((loginRes) => {
      cy.request({
        method: 'PATCH',
        url: '/api/auth/profile/',
        body: ORIGINAL,
        headers: { Authorization: `Bearer ${loginRes.body.tokens.access}` },
      })
    })
  })

  it('muestra el email y nombre del usuario', () => {
    cy.contains('Mi perfil').should('be.visible')
    cy.get('input[autocomplete=given-name]').should('have.value', ORIGINAL.first_name)
    cy.get('input[autocomplete=family-name]').should('have.value', ORIGINAL.last_name)
    cy.contains('cypress+e2e@personal-finance.local')
  })

  it('el botón Guardar está deshabilitado sin cambios', () => {
    cy.contains('button', 'Guardar cambios').should('be.disabled')
  })

  it('edita el nombre, guarda y refleja el cambio en el UserMenu', () => {
    const nuevoNombre = `Cy${Date.now().toString().slice(-4)}`
    cy.get('input[autocomplete=given-name]').clear().type(nuevoNombre)
    cy.contains('button', 'Guardar cambios').should('not.be.disabled').click()
    cy.get('input[autocomplete=given-name]').should('have.value', nuevoNombre)

    cy.contains('button', 'Volver').click()
    cy.url().should('eq', Cypress.config().baseUrl + '/')
    cy.contains(nuevoNombre).should('be.visible')
  })

  it('el botón Cancelar revierte los cambios', () => {
    cy.get('input[autocomplete=given-name]').clear().type('TEMP')
    cy.contains('button', 'Cancelar').click()
    cy.get('input[autocomplete=given-name]').should('have.value', ORIGINAL.first_name)
  })
})