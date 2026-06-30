describe('Cuentas', () => {
  const ACCOUNT_NAME = `Cuenta Cypress ${Date.now()}`
  let accessToken: string | null = null

  function deactivateAllActiveAccounts() {
    if (!accessToken) return cy.wrap(null)
    return cy
      .request({
        method: 'GET',
        url: '/api/accounts/',
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then((res) => {
        const accounts = res.body as Array<{ id: number; is_active: boolean }>
        const actives = accounts.filter((a) => a.is_active)
        if (actives.length === 0) return cy.wrap(null)
        return cy.wrap(actives).each((a: { id: number }) => {
          return cy.request({
            method: 'POST',
            url: `/api/accounts/${a.id}/deactivate/`,
            headers: { Authorization: `Bearer ${accessToken}` },
          })
        })
      })
  }

  function createAccountViaApi(input: {
    name: string
    account_type: string
    currency: string
    initial_balance: string
  }) {
    return cy.request({
      method: 'POST',
      url: '/api/accounts/',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: input,
    })
  }

  beforeEach(() => {
    cy.loginAsFixture('primary').then((res) => {
      accessToken = res.tokens.access
    })
  })

  after(() => {
    deactivateAllActiveAccounts()
  })

  it('visitar /accounts sin auth redirige a /login', () => {
    cy.clearAuth()
    cy.visit('/accounts')
    cy.url().should('include', '/login')
  })

  it('muestra la página de cuentas sin cuentas activas', () => {
    deactivateAllActiveAccounts().then(() => {
      cy.visit('/accounts')
      cy.contains('h1', 'Cuentas').should('be.visible')
      cy.contains('button', 'Nueva cuenta').should('be.visible')
      // No debe haber filas con estado Activo
      cy.get('main').contains('Activo').should('not.exist')
    })
  })

  it('crea una cuenta y aparece en la lista', () => {
    deactivateAllActiveAccounts().then(() => {
      cy.visit('/accounts')
      cy.contains('button', 'Nueva cuenta').click()
      cy.get('[role=dialog]').should('be.visible')
      cy.get('input[name="name"]').type(ACCOUNT_NAME)

      cy.get('[data-testid="account-type-select"]').click()
      cy.get('[role=option]').contains('Efectivo').click()

      cy.get('[data-testid="currency-select"]').click()
      cy.get('[role=option]').contains('Peso argentino').click()

      cy.get('input[name="initial_balance"]').clear().type('1000.50')

      cy.get('[role=dialog]').contains('button', 'Crear cuenta').click()

      cy.contains(ACCOUNT_NAME, { timeout: 10000 }).should('be.visible')
      cy.contains('Efectivo').should('be.visible')
      cy.contains('ARS').should('be.visible')
      cy.contains('Activo').should('be.visible')
    })
  })

  it('valida que el nombre sea obligatorio', () => {
    deactivateAllActiveAccounts().then(() => {
      cy.visit('/accounts')
      cy.contains('button', 'Nueva cuenta').click()
      cy.get('[role=dialog]').should('be.visible')
      cy.get('[role=dialog]').contains('button', 'Crear cuenta').click()
      cy.contains('El nombre de la cuenta es obligatorio').should('be.visible')
    })
  })

  it('rechaza nombre duplicado para cuenta activa', () => {
    deactivateAllActiveAccounts().then(() => {
      createAccountViaApi({
        name: ACCOUNT_NAME,
        account_type: 'cash',
        currency: 'ARS',
        initial_balance: '0',
      }).then(() => {
        cy.visit('/accounts')
        cy.contains(ACCOUNT_NAME, { timeout: 10000 }).should('be.visible')
        cy.contains('button', 'Nueva cuenta').click()
        cy.get('[role=dialog]').should('be.visible')
        cy.get('input[name="name"]').type(ACCOUNT_NAME)
        cy.get('[data-testid="account-type-select"]').click()
        cy.get('[role=option]').contains('Efectivo').click()
        cy.get('[data-testid="currency-select"]').click()
        cy.get('[role=option]').contains('Peso argentino').click()
        cy.get('[role=dialog]').contains('button', 'Crear cuenta').click()
        cy.get('[role=alert]', { timeout: 10000 }).should('be.visible')
        cy.contains('[role=alert]', /ya tenés una cuenta activa con ese nombre/i).should('be.visible')
      })
    })
  })

  it('edita el nombre de una cuenta', () => {
    deactivateAllActiveAccounts().then(() => {
      createAccountViaApi({
        name: ACCOUNT_NAME,
        account_type: 'bank',
        currency: 'USD',
        initial_balance: '500',
      }).then(() => {
        cy.visit('/accounts')
        cy.contains(ACCOUNT_NAME, { timeout: 10000 }).should('be.visible')

        cy.get(`button[aria-label="Editar ${ACCOUNT_NAME}"]`).first().click()
        cy.get('[role=dialog]').should('be.visible')
        cy.get('input[name="name"]').clear().type('Cuenta Editada')
        cy.get('[role=dialog]').contains('button', 'Guardar cambios').click()

        cy.contains('Cuenta Editada', { timeout: 10000 }).should('be.visible')
      })
    })
  })

  it('desactiva una cuenta y refleja el estado', () => {
    deactivateAllActiveAccounts().then(() => {
      createAccountViaApi({
        name: ACCOUNT_NAME,
        account_type: 'cash',
        currency: 'ARS',
        initial_balance: '0',
      }).then(() => {
        cy.visit('/accounts')
        cy.contains(ACCOUNT_NAME, { timeout: 10000 }).should('be.visible')
        cy.contains('Activo').should('be.visible')

        cy.get(`button[aria-label="Desactivar ${ACCOUNT_NAME}"]`).first().click()
        cy.contains('button', 'Sí').click()

        cy.contains('Inactivo', { timeout: 10000 }).should('be.visible')
      })
    })
  })

  it('activa una cuenta inactiva y refleja el estado', () => {
    deactivateAllActiveAccounts().then(() => {
      createAccountViaApi({
        name: ACCOUNT_NAME,
        account_type: 'cash',
        currency: 'ARS',
        initial_balance: '0',
      }).then((res) => {
        const accountId = res.body.id
        cy.request({
          method: 'POST',
          url: `/api/accounts/${accountId}/deactivate/`,
          headers: { Authorization: `Bearer ${accessToken}` },
        }).then(() => {
          cy.visit('/accounts')
          cy.contains(ACCOUNT_NAME, { timeout: 10000 }).should('be.visible')
          cy.contains('Inactivo').should('be.visible')

          cy.get(`button[aria-label="Activar ${ACCOUNT_NAME}"]`).first().click()
          cy.contains('button', 'Sí').click()

          cy.contains('Activo', { timeout: 10000 }).should('be.visible')
        })
      })
    })
  })
})