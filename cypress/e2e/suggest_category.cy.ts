describe('Sugerencia de categoría', () => {
  let accessToken: string | null = null

  type CategoryRef = { id: number; name: string }
  type AccountRef = { id: number }
  type RuleRef = { id: number }
  type Seed = {
    account: AccountRef
    category: CategoryRef
    rule: RuleRef
  }

  function todayISO(): string {
    const d = new Date()
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd}`
  }

  function authHeaders() {
    return { Authorization: `Bearer ${accessToken}` }
  }

  function deleteAllTransactions() {
    if (!accessToken) return cy.wrap(null)
    const collectAll = (
      pageNum: number,
      acc: Array<{ id: number; transfer_group_id: string | null }>,
    ): Cypress.Chainable<Array<{ id: number; transfer_group_id: string | null }>> =>
      cy
        .request({
          method: 'GET',
          url: `/api/transactions/?page=${pageNum}`,
          headers: authHeaders(),
        })
        .then((res: Cypress.Response<unknown>) => {
          const body = res.body as {
            results: Array<{ id: number; transfer_group_id: string | null }>
            next: string | null
          }
          const merged = acc.concat(body.results)
          if (body.next == null) return cy.wrap(merged)
          return collectAll(pageNum + 1, merged)
        })
    return collectAll(1, []).then(
      (txs: Array<{ id: number; transfer_group_id: string | null }>) => {
        const seenGroups = new Set<string>()
        const toDelete: number[] = []
        for (const t of txs) {
          if (t.transfer_group_id != null) {
            if (seenGroups.has(t.transfer_group_id)) continue
            seenGroups.add(t.transfer_group_id)
          }
          toDelete.push(t.id)
        }
        if (toDelete.length === 0) return cy.wrap(null)
        return cy.wrap(toDelete).each((id: number) => {
          return cy.request({
            method: 'DELETE',
            url: `/api/transactions/${id}/`,
            headers: authHeaders(),
          })
        })
      },
    )
  }

  function deleteAllRules() {
    if (!accessToken) return cy.wrap(null)
    return cy
      .request({
        method: 'GET',
        url: '/api/categorization-rules/',
        headers: authHeaders(),
      })
      .then((res: Cypress.Response<unknown>) => {
        const rules = res.body as Array<{ id: number }>
        if (rules.length === 0) return cy.wrap(null)
        return cy.wrap(rules).each((r: { id: number }) => {
          return cy.request({
            method: 'DELETE',
            url: `/api/categorization-rules/${r.id}/`,
            headers: authHeaders(),
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
        headers: authHeaders(),
      })
      .then((res: Cypress.Response<unknown>) => {
        const categories = res.body as Array<{ id: number; is_active: boolean }>
        const actives = categories.filter((c) => c.is_active)
        if (actives.length === 0) return cy.wrap(null)
        return cy.wrap(actives).each((c: { id: number }) => {
          return cy.request({
            method: 'POST',
            url: `/api/categories/${c.id}/deactivate/`,
            headers: authHeaders(),
          })
        })
      })
  }

  function deactivateAllActiveAccounts() {
    if (!accessToken) return cy.wrap(null)
    return cy
      .request({
        method: 'GET',
        url: '/api/accounts/',
        headers: authHeaders(),
      })
      .then((res: Cypress.Response<unknown>) => {
        const accounts = res.body as Array<{ id: number; is_active: boolean }>
        const actives = accounts.filter((a) => a.is_active)
        if (actives.length === 0) return cy.wrap(null)
        return cy.wrap(actives).each((a: { id: number }) => {
          return cy.request({
            method: 'POST',
            url: `/api/accounts/${a.id}/deactivate/`,
            headers: authHeaders(),
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
      headers: authHeaders(),
      body: input,
    })
  }

  function createCategoryViaApi(input: { name: string; kind: string }) {
    return cy.request({
      method: 'POST',
      url: '/api/categories/',
      headers: authHeaders(),
      body: input,
    })
  }

  function createRuleViaApi(input: {
    pattern: string
    match_type: string
    category_id: number
    kind: string
    priority: number
  }) {
    return cy.request({
      method: 'POST',
      url: '/api/categorization-rules/',
      headers: authHeaders(),
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
      headers: authHeaders(),
      body: input,
    })
  }

  function seedWorld() {
    const result: Partial<Seed> = {}
    return cy.wrap(null).then(() => {
      return deleteAllRules()
        .then(() => deactivateAllActiveAccounts())
        .then(() => deactivateAllActiveCategories())
        .then(() =>
          createAccountViaApi({
            name: 'Efectivo Sugerencia E2E',
            account_type: 'cash',
            currency: 'ARS',
            initial_balance: '1000',
          }),
        )
        .then((res: Cypress.Response<unknown>) => {
          result.account = res.body as AccountRef
          return createCategoryViaApi({ name: 'Comida E2E', kind: 'expense' })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.category = res.body as CategoryRef
          return createRuleViaApi({
            pattern: 'coto',
            match_type: 'contains',
            category_id: result.category!.id,
            kind: 'expense',
            priority: 5,
          })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.rule = res.body as RuleRef
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
    deleteAllTransactions()
      .then(() => deleteAllRules())
      .then(() => deactivateAllActiveCategories())
      .then(() => deactivateAllActiveAccounts())
  })

  it('crea una regla y sugiere la categoría inline en /transactions', () => {
    const txDescription = `COMPRA COTO ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedWorld())
      .then(({ account, category }: Seed) => {
        createTransactionViaApi({
          account_id: account.id,
          kind: 'expense',
          amount: '1500',
          date: todayISO(),
          description: txDescription,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(txDescription, { timeout: 15000 }).should('be.visible')

        // Abrir el dropdown de la primera fila sin categoría
        cy.get('main table tbody tr')
          .first()
          .find('button')
          .contains('Sin categoría')
          .click()

        // Aparece la sugerencia "Usar Comida E2E"
        cy.get('[role="menu"]')
          .contains('Usar Comida E2E')
          .should('be.visible')
          .click()

        // Tras aplicar, la celda muestra el nombre de la categoría
        cy.contains(txDescription, { timeout: 15000 }).should('be.visible')
        cy.get('main table tbody tr')
          .first()
          .contains('Comida E2E')
          .should('be.visible')
      })
  })

  it('muestra "Sin sugerencia" cuando no hay regla que matchee', () => {
    const txDescription = `Sin match ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedWorld())
      .then(({ account }: Seed) => {
        createTransactionViaApi({
          account_id: account.id,
          kind: 'expense',
          amount: '200',
          date: todayISO(),
          description: txDescription,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(txDescription, { timeout: 15000 }).should('be.visible')

        cy.get('main table tbody tr')
          .first()
          .find('button')
          .contains('Sin categoría')
          .click()

        cy.get('[role="menu"]').contains('Sin sugerencia').should('be.visible')
      })
  })
})