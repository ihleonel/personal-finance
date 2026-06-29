describe('Perfil', () => {
  const ORIGINAL = { first_name: 'Cy', last_name: 'Press' }
  const PRIMARY_EMAIL = 'cypress+e2e@personal-finance.local'
  const PRIMARY_PASSWORD = 'Cypress12345'
  const NEW_PASSWORD = 'NewPass12345'

  beforeEach(() => {
    // restaurar contraseña a la original si un test anterior la cambió
    cy.request({
      method: 'POST',
      url: '/api/auth/login/',
      failOnStatusCode: false,
      body: { email: PRIMARY_EMAIL, password: PRIMARY_PASSWORD },
    }).then((res) => {
      if (res.status !== 200) {
        // la contraseña primaria no funciona => fue cambiada, restaurar con NEW
        cy.request({
          method: 'POST',
          url: '/api/auth/login/',
          body: { email: PRIMARY_EMAIL, password: NEW_PASSWORD },
        }).then((r) => {
          cy.request({
            method: 'POST',
            url: '/api/auth/change-password/',
            headers: { Authorization: `Bearer ${r.body.tokens.access}` },
            body: { current_password: NEW_PASSWORD, new_password: PRIMARY_PASSWORD },
          })
        })
      }
    })
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
    // restaurar estado al final de toda la suite (perfil y contraseña)
    cy.request({
      method: 'POST',
      url: '/api/auth/login/',
      failOnStatusCode: false,
      body: { email: PRIMARY_EMAIL, password: PRIMARY_PASSWORD },
    }).then((res) => {
      let loginRes = res
      if (res.status !== 200) {
        // la contraseña quedó cambiada, restaurar con NEW
        return cy
          .request({
            method: 'POST',
            url: '/api/auth/login/',
            body: { email: PRIMARY_EMAIL, password: NEW_PASSWORD },
          })
          .then((r) => {
            return cy.request({
              method: 'POST',
              url: '/api/auth/change-password/',
              headers: { Authorization: `Bearer ${r.body.tokens.access}` },
              body: { current_password: NEW_PASSWORD, new_password: PRIMARY_PASSWORD },
            })
          })
          .then(() => {
            // re-login con la contraseña primaria restaurada
            return cy.request('POST', '/api/auth/login/', {
              email: PRIMARY_EMAIL,
              password: PRIMARY_PASSWORD,
            })
          })
      }
      return cy.request({
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

  describe('Cambio de contraseña', () => {
    it('muestra el card de seguridad con tres campos', () => {
      cy.contains('Seguridad').should('be.visible')
      cy.get('input[aria-label="Contraseña actual"]').should('exist')
      cy.get('input[aria-label="Nueva contraseña"]').should('exist')
      cy.get('input[aria-label="Confirmar nueva contraseña"]').should('exist')
      cy.contains('button', 'Cambiar contraseña').should('be.disabled')
    })

    it('valida que la nueva contraseña tenga mínimo 8 caracteres', () => {
      cy.get('input[aria-label="Contraseña actual"]').type(PRIMARY_PASSWORD)
      cy.get('input[aria-label="Nueva contraseña"]').type('Short1')
      cy.get('input[aria-label="Confirmar nueva contraseña"]').type('Short1')
      cy.contains('button', 'Cambiar contraseña').click()
      cy.contains(/al menos 8 caracteres/i).should('be.visible')
      // no se llama al backend: no aparece toast de éxito
      cy.contains('Contraseña actualizada').should('not.exist')
    })

    it('valida que las contraseñas nuevas coincidan', () => {
      cy.get('input[aria-label="Contraseña actual"]').type(PRIMARY_PASSWORD)
      cy.get('input[aria-label="Nueva contraseña"]').type(NEW_PASSWORD)
      cy.get('input[aria-label="Confirmar nueva contraseña"]').type('Different123')
      cy.contains('button', 'Cambiar contraseña').click()
      cy.contains(/no coinciden/i).should('be.visible')
    })

    it('muestra error cuando la contraseña actual es incorrecta', () => {
      cy.get('input[aria-label="Contraseña actual"]').type('WrongOld123')
      cy.get('input[aria-label="Nueva contraseña"]').type(NEW_PASSWORD)
      cy.get('input[aria-label="Confirmar nueva contraseña"]').type(NEW_PASSWORD)
      cy.contains('button', 'Cambiar contraseña').click()
      cy.get('[role=alert]', { timeout: 10000 }).should('be.visible')
      cy.contains('[role=alert]', /contraseña actual es incorrecta/i).should('be.visible')
      cy.url().should('include', '/profile')
    })

    it('cambia la contraseña exitosamente y mantiene la sesión', () => {
      cy.get('input[aria-label="Contraseña actual"]').type(PRIMARY_PASSWORD)
      cy.get('input[aria-label="Nueva contraseña"]').type(NEW_PASSWORD)
      cy.get('input[aria-label="Confirmar nueva contraseña"]').type(NEW_PASSWORD)
      cy.contains('button', 'Cambiar contraseña').click()
      cy.contains('Contraseña actualizada', { timeout: 10000 }).should('be.visible')
      // los inputs se limpian
      cy.get('input[aria-label="Contraseña actual"]').should('have.value', '')
      cy.get('input[aria-label="Nueva contraseña"]').should('have.value', '')
      cy.get('input[aria-label="Confirmar nueva contraseña"]').should('have.value', '')
      // el botón vuelve a estar deshabilitado
      cy.contains('button', 'Cambiar contraseña').should('be.disabled')
      // sigue en /profile (no se deslogueó)
      cy.url().should('include', '/profile')
      cy.contains('Mi perfil').should('be.visible')
      // la nueva contraseña funciona en el backend
      cy.request('POST', '/api/auth/login/', {
        email: PRIMARY_EMAIL,
        password: NEW_PASSWORD,
      }).then((res) => {
        expect(res.status).to.eq(200)
      })
    })

    it('rechaza contraseña nueva igual a la actual', () => {
      cy.get('input[aria-label="Contraseña actual"]').type(PRIMARY_PASSWORD)
      cy.get('input[aria-label="Nueva contraseña"]').type(PRIMARY_PASSWORD)
      cy.get('input[aria-label="Confirmar nueva contraseña"]').type(PRIMARY_PASSWORD)
      cy.contains('button', 'Cambiar contraseña').click()
      cy.get('[role=alert]', { timeout: 10000 }).should('be.visible')
      cy.contains('[role=alert]', /no puede ser igual a la contraseña actual/i).should('be.visible')
    })
  })
})