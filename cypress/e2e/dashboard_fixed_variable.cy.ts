describe('Dashboard - Gastos fijos vs variables', () => {
  let accessToken: string | null = null

  type AccountRef = { id: number }
  type CategoryRef = { id: number; is_fixed: boolean }

  function todayISO(): string {
    const d = new Date()
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd}`
  }

  function deactivateAllActiveAccounts() {
    if (!accessToken) return cy.wrap(null)
    return cy
      .request({
        method: 'GET',
        url: '/api/accounts/',
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then((res: Cypress.Response<unknown>) => {
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

  function deactivateAllActiveCategories() {
    if (!accessToken) return cy.wrap(null)
    return cy
      .request({
        method: 'GET',
        url: '/api/categories/',
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then((res: Cypress.Response<unknown>) => {
        const categories = res.body as Array<{ id: number; is_active: boolean }>
        const actives = categories.filter((c) => c.is_active)
        if (actives.length === 0) return cy.wrap(null)
        return cy.wrap(actives).each((c: { id: number }) => {
          return cy.request({
            method: 'POST',
            url: `/api/categories/${c.id}/deactivate/`,
            headers: { Authorization: `Bearer ${accessToken}` },
          })
        })
      })
  }

  function deleteAllTransactions() {
    if (!accessToken) return cy.wrap(null)
    const collectIds = (
      pageNum: number,
      acc: number[],
    ): Cypress.Chainable<number[]> =>
      cy
        .request({
          method: 'GET',
          url: `/api/transactions/?page=${pageNum}`,
          headers: { Authorization: `Bearer ${accessToken}` },
        })
        .then((res: Cypress.Response<unknown>) => {
          const body = res.body as {
            results: Array<{ id: number }>
            next: string | null
          }
          const ids = acc.concat(body.results.map((t) => t.id))
          if (body.next == null) return cy.wrap(ids)
          return collectIds(pageNum + 1, ids)
        })
    return collectIds(1, []).then((ids: number[]) => {
      if (ids.length === 0) return cy.wrap(null)
      return cy.wrap(ids).each((id: number) => {
        return cy.request({
          method: 'DELETE',
          url: `/api/transactions/${id}/`,
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

  function createCategoryViaApi(input: {
    name: string
    kind: string
    is_fixed?: boolean
  }) {
    return cy.request({
      method: 'POST',
      url: '/api/categories/',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: input,
    })
  }

  function createTransactionViaApi(input: {
    account_id: number
    kind: string
    amount: string
    date: string
    description?: string
    category_id?: number | null
  }) {
    return cy.request({
      method: 'POST',
      url: '/api/transactions/',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: input,
    })
  }

  type Seed = {
    account: AccountRef
    fixedCategory: CategoryRef
    variableCategory: CategoryRef
  }

  function seedAccountAndCategories() {
    const result: Partial<Seed> = {}
    return cy.wrap(null).then(() => {
      return deactivateAllActiveAccounts()
        .then(() => deactivateAllActiveCategories())
        .then(() =>
          createAccountViaApi({
            name: 'Efectivo FV',
            account_type: 'cash',
            currency: 'ARS',
            initial_balance: '0',
          }),
        )
        .then((res: Cypress.Response<unknown>) => {
          result.account = res.body as AccountRef
          return createCategoryViaApi({
            name: 'Alquiler FV',
            kind: 'expense',
            is_fixed: true,
          })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.fixedCategory = res.body as CategoryRef
          return createCategoryViaApi({
            name: 'Salidas FV',
            kind: 'expense',
            is_fixed: false,
          })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.variableCategory = res.body as CategoryRef
          return cy.wrap(result as Seed)
        })
    })
  }

  beforeEach(() => {
    cy.loginAsFixture('primary').then((res) => {
      accessToken = res.tokens.access
    })
  })

  after(() => {
    deleteAllTransactions().then(() =>
      deactivateAllActiveCategories().then(() => deactivateAllActiveAccounts()),
    )
  })

  it('muestra la sección con los totales fijos y variables del periodo actual', () => {
    deleteAllTransactions()
      .then(() => seedAccountAndCategories())
      .then(({ account, fixedCategory, variableCategory }: Seed) => {
        createTransactionViaApi({
          account_id: account.id,
          kind: 'expense',
          amount: '500',
          date: todayISO(),
          description: 'Pago alquiler',
          category_id: fixedCategory.id,
        })
        createTransactionViaApi({
          account_id: account.id,
          kind: 'expense',
          amount: '120.50',
          date: todayISO(),
          description: 'Cena con amigos',
          category_id: variableCategory.id,
        })
      })
      .then(() => {
        cy.visit('/')
        cy.contains('h1', /Dashboard/i).should('be.visible')
        cy.contains('Gastos fijos vs variables por periodo', { timeout: 15000 }).should(
          'be.visible',
        )

        cy.get('[data-testid="fv-fixed-row"]').within(() => {
          cy.contains('Gastos fijos').should('be.visible')
        })
        cy.get('[data-testid="fv-variable-row"]').within(() => {
          cy.contains('Gastos variables').should('be.visible')
        })

        // Totals row last column = current period, must equal -620.50
        // (the (parcial) marker is on the last header column).
        cy.get('[data-testid="fv-totals-row"]').within(() => {
          cy.contains('-620,50').should('be.visible')
        })
        // Fijos -500 and variables -120.50 present too
        cy.get('[data-testid="fv-fixed-row"]').contains('-500,00').should('be.visible')
        cy.get('[data-testid="fv-variable-row"]').contains('-120,50').should('be.visible')
      })
  })

  it('muestra "—" cuando no hay gastos fijos ni variables', () => {
    deleteAllTransactions()
      .then(() => deactivateAllActiveCategories())
      .then(() => {
        createCategoryViaApi({ name: 'Sueldo FV', kind: 'income', is_fixed: false })
      })
      .then(() => {
        cy.visit('/')
        cy.contains('Gastos fijos vs variables por periodo', { timeout: 15000 }).should(
          'be.visible',
        )
        cy.get('[data-testid="fv-fixed-row"]').within(() => {
          cy.contains('—').should('exist')
        })
        cy.get('[data-testid="fv-variable-row"]').within(() => {
          cy.contains('—').should('exist')
        })
      })
  })
})
