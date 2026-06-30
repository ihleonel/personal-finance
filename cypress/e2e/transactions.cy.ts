describe('Transacciones', () => {
  const TX_DESCRIPTION = `Tx Cypress ${Date.now()}`
  let accessToken: string | null = null

  type AccountRef = { id: number }
  type CategoryRef = { id: number }
  type Seed = {
    account1: AccountRef
    account2: AccountRef
    incomeCategory: CategoryRef
    expenseCategory: CategoryRef
  }

  function todayISO(): string {
    const d = new Date()
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd}`
  }

  function yesterdayISO(): string {
    const d = new Date()
    d.setDate(d.getDate() - 1)
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
    const collectAll = (
      pageNum: number,
      acc: Array<{ id: number; transfer_group_id: string | null }>,
    ): Cypress.Chainable<Array<{ id: number; transfer_group_id: string | null }>> =>
      cy
        .request({
          method: 'GET',
          url: `/api/transactions/?page=${pageNum}`,
          headers: { Authorization: `Bearer ${accessToken}` },
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
    return collectAll(1, []).then((txs: Array<{ id: number; transfer_group_id: string | null }>) => {
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

  function createCategoryViaApi(input: { name: string; kind: string }) {
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

  function createTransferViaApi(input: {
    source_account_id: number
    destination_account_id: number
    amount: string
    date: string
    description?: string
  }) {
    return cy.request({
      method: 'POST',
      url: '/api/transactions/transfer/',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: input,
    })
  }

  function seedAccountsAndCategories() {
    const result: Partial<Seed> = {}
    return cy.wrap(null).then(() => {
      return deactivateAllActiveAccounts()
        .then(() => deactivateAllActiveCategories())
        .then(() =>
          createAccountViaApi({
            name: 'Efectivo E2E',
            account_type: 'cash',
            currency: 'ARS',
            initial_balance: '1000',
          }),
        )
        .then((res: Cypress.Response<unknown>) => {
          result.account1 = res.body as AccountRef
          return createAccountViaApi({
            name: 'Banco E2E',
            account_type: 'bank',
            currency: 'ARS',
            initial_balance: '5000',
          })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.account2 = res.body as AccountRef
          return createCategoryViaApi({ name: 'Sueldo E2E', kind: 'income' })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.incomeCategory = res.body as CategoryRef
          return createCategoryViaApi({ name: 'Comida E2E', kind: 'expense' })
        })
        .then((res: Cypress.Response<unknown>) => {
          result.expenseCategory = res.body as CategoryRef
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

  it('visitar /transactions sin auth redirige a /login', () => {
    cy.clearAuth()
    cy.visit('/transactions')
    cy.url().should('include', '/login')
  })

  it('muestra la página de transacciones vacía', () => {
    deleteAllTransactions().then(() => {
      cy.visit('/transactions')
      cy.contains('h1', 'Transacciones').should('be.visible')
      cy.contains('button', 'Nueva transacción').should('be.visible')
      cy.contains('button', 'Nueva transferencia').should('be.visible')
      cy.contains('No tenés transacciones todavía').should('be.visible')
    })
  })

  it('crea una transacción de ingreso y aparece en la lista', () => {
    deleteAllTransactions().then(() => seedAccountsAndCategories()).then(() => {
      cy.visit('/transactions')
      cy.contains('button', 'Nueva transacción').click()
      cy.get('[role=dialog]').should('be.visible')

      cy.get('[data-testid="tx-kind-select"]').click()
      cy.get('[role=option]').contains('Ingreso').click()

      cy.get('[data-testid="tx-account-select"]').click()
      cy.get('[role=option]').contains('Efectivo E2E').click()

      cy.get('[data-testid="tx-amount-input"]').type('1000')
      cy.get('[data-testid="tx-description-input"]').type(TX_DESCRIPTION)

      cy.get('[role=dialog]').contains('button', 'Crear transacción').click()

      cy.contains(TX_DESCRIPTION, { timeout: 15000 }).should('be.visible')
      cy.contains('Ingreso').should('be.visible')
    })
  })

  it('crea una transacción de egreso y aparece en la lista', () => {
    const desc = `Egreso ${Date.now()}`
    deleteAllTransactions().then(() => seedAccountsAndCategories()).then(() => {
      cy.visit('/transactions')
      cy.contains('button', 'Nueva transacción').click()
      cy.get('[role=dialog]').should('be.visible')

      cy.get('[data-testid="tx-kind-select"]').click()
      cy.get('[role=option]').contains('Egreso').click()

      cy.get('[data-testid="tx-account-select"]').click()
      cy.get('[role=option]').contains('Banco E2E').click()

      cy.get('[data-testid="tx-amount-input"]').type('500.50')
      cy.get('[data-testid="tx-description-input"]').type(desc)

      cy.get('[role=dialog]').contains('button', 'Crear transacción').click()

      cy.contains(desc, { timeout: 15000 }).should('be.visible')
      cy.contains('Egreso').should('be.visible')
    })
  })

  it('crea una transacción con categoría y aparece en la lista', () => {
    const desc = `Con cat ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1, incomeCategory }: Seed) => {
        cy.visit('/transactions')
        cy.contains('button', 'Nueva transacción').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="tx-kind-select"]').click()
        cy.get('[role=option]').contains('Ingreso').click()

        cy.get('[data-testid="tx-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.get('[data-testid="tx-category-select"]').click()
        cy.get('[role=option]').contains('Sueldo E2E').click()

        cy.get('[data-testid="tx-amount-input"]').type('2000')
        cy.get('[data-testid="tx-description-input"]').type(desc)

        cy.get('[role=dialog]').contains('button', 'Crear transacción').click()

        cy.contains(desc, { timeout: 15000 }).should('be.visible')
        cy.contains('Sueldo E2E').should('be.visible')
      })
  })

  it('valida que el monto sea obligatorio', () => {
    deleteAllTransactions().then(() => seedAccountsAndCategories()).then(() => {
      cy.visit('/transactions')
      cy.contains('button', 'Nueva transacción').click()
      cy.get('[role=dialog]').should('be.visible')

      cy.get('[data-testid="tx-kind-select"]').click()
      cy.get('[role=option]').contains('Ingreso').click()

      cy.get('[data-testid="tx-account-select"]').click()
      cy.get('[role=option]').contains('Efectivo E2E').click()

      cy.get('[role=dialog]').contains('button', 'Crear transacción').click()

      cy.contains('El monto es obligatorio.').should('be.visible')
    })
  })

  it('crea una transferencia entre dos cuentas y aparecen ambas filas', () => {
    const desc = `Transfer ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(() => {
        cy.visit('/transactions')
        cy.contains('button', 'Nueva transferencia').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="transfer-source-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.get('[data-testid="transfer-destination-select"]').click()
        cy.get('[role=option]').contains('Banco E2E').click()

        cy.get('[data-testid="transfer-amount-input"]').type('300')
        cy.get('[data-testid="transfer-description-input"]').type(desc)

        cy.get('[role=dialog]').contains('button', 'Crear transferencia').click()

        // Ambas filas tienen badge "Transferencia"
        cy.contains(desc, { timeout: 15000 }).should('be.visible')
        cy.get('main')
          .contains('Transferencia')
          .should('be.visible')
        cy.get('main').find('span').contains('Transferencia').should('have.length.at.least', 1)
      })
  })

  it('rechaza transferencia con misma cuenta origen y destino', () => {
    deleteAllTransactions().then(() => seedAccountsAndCategories()).then(() => {
      cy.visit('/transactions')
      cy.contains('button', 'Nueva transferencia').click()
      cy.get('[role=dialog]').should('be.visible')

      // Selecciona mismo account en origen y destino
      cy.get('[data-testid="transfer-source-select"]').click()
      cy.get('[role=option]').contains('Efectivo E2E').click()

      cy.get('[data-testid="transfer-destination-select"]').click()
      cy.get('[role=option]').contains('Efectivo E2E').click()

      cy.get('[data-testid="transfer-amount-input"]').type('100')

      cy.get('[role=dialog]').contains('button', 'Crear transferencia').click()

      cy.contains('La cuenta de origen y destino no pueden ser la misma.').should('be.visible')
    })
  })

  it('valida que el monto sea obligatorio en transferencia', () => {
    deleteAllTransactions().then(() => seedAccountsAndCategories()).then(() => {
      cy.visit('/transactions')
      cy.contains('button', 'Nueva transferencia').click()
      cy.get('[role=dialog]').should('be.visible')

      cy.get('[data-testid="transfer-source-select"]').click()
      cy.get('[role=option]').contains('Efectivo E2E').click()

      cy.get('[data-testid="transfer-destination-select"]').click()
      cy.get('[role=option]').contains('Banco E2E').click()

      cy.get('[role=dialog]').contains('button', 'Crear transferencia').click()

      cy.contains('El monto es obligatorio.').should('be.visible')
    })
  })

  it('edita el monto de una transacción', () => {
    const desc = `Edit monto ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'income',
          amount: '100',
          date: todayISO(),
          description: desc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc, { timeout: 15000 }).should('be.visible')

        cy.get('button[aria-label="Editar transacción"]').first().click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="tx-amount-input"]').clear().type('250')
        cy.get('[role=dialog]').contains('button', 'Guardar cambios').click()

        cy.contains('250,00', { timeout: 15000 }).should('be.visible')
      })
  })

  it('edita la descripción de una transacción', () => {
    const desc = `Edit desc ${Date.now()}`
    const newDesc = `Desc nueva ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'expense',
          amount: '50',
          date: todayISO(),
          description: desc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc, { timeout: 15000 }).should('be.visible')

        cy.get('button[aria-label="Editar transacción"]').first().click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="tx-description-input"]').clear().type(newDesc)
        cy.get('[role=dialog]').contains('button', 'Guardar cambios').click()

        cy.contains(newDesc, { timeout: 15000 }).should('be.visible')
        cy.get('main').contains(desc).should('not.exist')
      })
  })

  it('no permite editar una transacción que es parte de una transferencia', () => {
    const desc = `No edit transfer ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1, account2 }: Seed) => {
        createTransferViaApi({
          source_account_id: account1.id,
          destination_account_id: account2.id,
          amount: '200',
          date: todayISO(),
          description: desc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc, { timeout: 15000 }).should('be.visible')
        // Las filas de transferencia NO tienen botón de editar
        cy.get('button[aria-label="Editar transacción"]').should('not.exist')
        cy.get('button[aria-label="Eliminar transacción"]').should('be.visible')
      })
  })

  it('elimina una transacción simple', () => {
    const desc = `Delete simple ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'income',
          amount: '100',
          date: todayISO(),
          description: desc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc, { timeout: 15000 }).should('be.visible')

        cy.get('button[aria-label="Eliminar transacción"]').first().click()
        cy.contains('button', 'Sí').click()

        cy.get('main').contains(desc).should('not.exist')
      })
  })

  it('elimina una transferencia y borra ambas filas', () => {
    const desc = `Delete transfer ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1, account2 }: Seed) => {
        createTransferViaApi({
          source_account_id: account1.id,
          destination_account_id: account2.id,
          amount: '200',
          date: todayISO(),
          description: desc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc, { timeout: 15000 }).should('be.visible')
        cy.contains('Transferencia').should('be.visible')

        cy.get('button[aria-label="Eliminar transacción"]').first().click()
        cy.contains('button', 'Sí').click()

        cy.get('main').contains(desc).should('not.exist')
        cy.get('main').contains('Transferencia').should('not.exist')
      })
  })

  it('cancela la eliminación de una transacción', () => {
    const desc = `Cancel delete ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'income',
          amount: '100',
          date: todayISO(),
          description: desc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc, { timeout: 15000 }).should('be.visible')

        cy.get('button[aria-label="Eliminar transacción"]').first().click()
        cy.contains('button', 'No').click()

        cy.contains(desc).should('be.visible')
      })
  })

  it('filtra transacciones por tipo ingreso', () => {
    const incomeDesc = `Filter income ${Date.now()}`
    const expenseDesc = `Filter expense ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1, account2 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'income',
          amount: '100',
          date: todayISO(),
          description: incomeDesc,
        })
        createTransactionViaApi({
          account_id: account2.id,
          kind: 'expense',
          amount: '50',
          date: todayISO(),
          description: expenseDesc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(incomeDesc, { timeout: 15000 }).should('be.visible')
        cy.contains(expenseDesc).should('be.visible')

        cy.get('[data-testid="filter-kind-select"]').click()
        cy.get('[role=option]').contains('Ingreso').click()

        cy.contains(incomeDesc, { timeout: 15000 }).should('be.visible')
        cy.get('main').contains(expenseDesc).should('not.exist')

        cy.contains('button', 'Limpiar').click()
        cy.contains(expenseDesc, { timeout: 15000 }).should('be.visible')
      })
  })

  it('filtra transacciones por cuenta', () => {
    const desc1 = `Filter acct1 ${Date.now()}`
    const desc2 = `Filter acct2 ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1, account2 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'income',
          amount: '100',
          date: todayISO(),
          description: desc1,
        })
        createTransactionViaApi({
          account_id: account2.id,
          kind: 'income',
          amount: '200',
          date: todayISO(),
          description: desc2,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(desc1, { timeout: 15000 }).should('be.visible')
        cy.contains(desc2).should('be.visible')

        cy.get('[data-testid="filter-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.contains(desc1, { timeout: 15000 }).should('be.visible')
        cy.get('main').contains(desc2).should('not.exist')

        cy.contains('button', 'Limpiar').click()
        cy.contains(desc2, { timeout: 15000 }).should('be.visible')
      })
  })

  it('filtra transacciones por rango de fechas', () => {
    const oldDesc = `Filter old ${Date.now()}`
    const todayDesc = `Filter today ${Date.now()}`
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1, account2 }: Seed) => {
        createTransactionViaApi({
          account_id: account1.id,
          kind: 'income',
          amount: '100',
          date: yesterdayISO(),
          description: oldDesc,
        })
        createTransactionViaApi({
          account_id: account2.id,
          kind: 'income',
          amount: '200',
          date: todayISO(),
          description: todayDesc,
        })
      })
      .then(() => {
        cy.visit('/transactions')
        cy.contains(oldDesc, { timeout: 15000 }).should('be.visible')
        cy.contains(todayDesc).should('be.visible')

        // Filtrar solo hoy
        cy.get('[data-testid="filter-date-from"]').type(todayISO())
        cy.get('[data-testid="filter-date-to"]').type(todayISO())

        cy.contains(todayDesc, { timeout: 15000 }).should('be.visible')
        cy.get('main').contains(oldDesc).should('not.exist')

        cy.contains('button', 'Limpiar').click()
        cy.contains(oldDesc, { timeout: 15000 }).should('be.visible')
      })
  })

  // ---------------------------------------------------------------------------
  // Importación masiva de transacciones desde CSV
  // ---------------------------------------------------------------------------

  it('importa un reporte de Macro y muestra el resumen', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/report_macro.csv',
        )
        cy.get('[data-testid="import-submit"]').click()

        cy.get('[data-testid="import-result-panel"]', { timeout: 15000 }).should('be.visible')
        cy.get('[data-testid="import-summary-created"]').should('contain', '67')
        cy.get('[data-testid="import-summary-errors"]').should('contain', '0')

        cy.get('[data-testid="import-close"]').click()

        cy.wrap(null).then(() => {
          const findInPages = (
            pageNum: number,
          ): Cypress.Chainable<unknown> =>
            cy
              .request({
                method: 'GET',
                url: `/api/transactions/?page=${pageNum}`,
                headers: { Authorization: `Bearer ${accessToken}` },
              })
              .then((res: Cypress.Response<unknown>) => {
                const body = res.body as {
                  results: Array<{ description: string }>
                  next: string | null
                }
                const found = body.results.some(
                  (r) => r.description === 'OUTSOURCE ARGENTINA SAS',
                )
                if (found) return cy.wrap(true)
                if (body.next == null) return cy.wrap(false)
                return findInPages(pageNum + 1)
              })
          return findInPages(1).should('eq', true)
        })
      })
  })

  it('importa un reporte de Mercado Pago y muestra el resumen', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account2 }: Seed) => {
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Banco E2E').click()

        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/report_mercado_pago.csv',
        )
        cy.get('[data-testid="import-submit"]').click()

        cy.get('[data-testid="import-result-panel"]', { timeout: 15000 }).should('be.visible')
        cy.get('[data-testid="import-summary-created"]').should('contain', '58')
        cy.get('[data-testid="import-summary-errors"]').should('contain', '0')

        cy.get('[data-testid="import-close"]').click()

        cy.wrap(null).then(() => {
          const findInPages = (
            pageNum: number,
          ): Cypress.Chainable<unknown> =>
            cy
              .request({
                method: 'GET',
                url: `/api/transactions/?page=${pageNum}`,
                headers: { Authorization: `Bearer ${accessToken}` },
              })
              .then((res: Cypress.Response<unknown>) => {
                const body = res.body as {
                  results: Array<{ description: string }>
                  next: string | null
                }
                const found = body.results.some(
                  (r) => r.description === 'Rendimientos',
                )
                if (found) return cy.wrap(true)
                if (body.next == null) return cy.wrap(false)
                return findInPages(pageNum + 1)
              })
          return findInPages(1).should('eq', true)
        })
      })
  })

  it('importa el mismo reporte dos veces y saltea los duplicados', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        // Primera importación
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')
        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()
        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/report_macro.csv',
        )
        cy.get('[data-testid="import-submit"]').click()
        cy.get('[data-testid="import-summary-created"]', { timeout: 15000 }).should('contain', '67')
        cy.get('[data-testid="import-close"]').click()

        // Contar filas tras primera importación (página 1 de 30)
        cy.get('main table tbody tr', { timeout: 15000 }).should('have.length', 30)
        cy.get('[data-testid="tx-pagination-info"]').should('contain', '67')

        // Segunda importación del mismo archivo a la misma cuenta
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')
        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()
        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/report_macro.csv',
        )
        cy.get('[data-testid="import-submit"]').click()

        cy.get('[data-testid="import-summary-created"]', { timeout: 15000 }).should('contain', '0')
        cy.get('[data-testid="import-summary-skipped"]').should('contain', '67')
        cy.get('[data-testid="import-close"]').click()

        // No se duplicaron filas: sigue habiendo 67 totales, 30 en página 1
        cy.get('main table tbody tr', { timeout: 15000 }).should('have.length', 30)
        cy.get('[data-testid="tx-pagination-info"]').should('contain', '67')
      })
  })

  it('rechaza un archivo con formato no soportado', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(() => {
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/report_unsupported.csv',
        )
        cy.get('[data-testid="import-submit"]').click()

        cy.contains('El formato del archivo no está soportado.').should('be.visible')
        cy.get('[data-testid="import-result-panel"]').should('not.exist')
      })
  })

  it('valida que el archivo sea obligatorio', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(() => {
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        // No se adjunta archivo
        cy.get('[data-testid="import-submit"]').click()

        cy.contains('Seleccioná un archivo CSV.').should('be.visible')
        cy.get('[data-testid="import-result-panel"]').should('not.exist')
      })
  })

  it('valida extensión .csv', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(() => {
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/not-a-csv.txt',
        )
        cy.get('[data-testid="import-submit"]').click()

        cy.contains('El archivo debe tener extensión .csv.').should('be.visible')
        cy.get('[data-testid="import-result-panel"]').should('not.exist')
      })
  })

  it('muestra lista de errores cuando hay filas inválidas', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        cy.visit('/transactions')
        cy.contains('button', 'Importar').click()
        cy.get('[role=dialog]').should('be.visible')

        cy.get('[data-testid="import-account-select"]').click()
        cy.get('[role=option]').contains('Efectivo E2E').click()

        cy.get('[data-testid="import-file-input"]').selectFile(
          'fixtures/report_macro_with_errors.csv',
        )
        cy.get('[data-testid="import-submit"]').click()

        cy.get('[data-testid="import-result-panel"]', { timeout: 15000 }).should('be.visible')
        cy.get('[data-testid="import-summary-created"]').should('contain', '2')
        cy.get('[data-testid="import-summary-errors"]').should('contain', '1')
        cy.get('[data-testid="import-errors-list"]').should('be.visible')
        cy.get('[data-testid="import-errors-list"]').contains('Fila').should('be.visible')

        cy.get('[data-testid="import-close"]').click()
        cy.contains('OUTSOURCE ARGENTINA SAS', { timeout: 15000 }).should('be.visible')
      })
  })

  it('pagina transacciones cuando hay más de 30', () => {
    deleteAllTransactions()
      .then(() => seedAccountsAndCategories())
      .then(({ account1 }: Seed) => {
        const create35 = (i: number): Cypress.Chainable<unknown> => {
          if (i >= 35) return cy.wrap(null)
          return createTransactionViaApi({
            account_id: account1.id,
            kind: 'income',
            amount: '10',
            date: todayISO(),
            description: `Pag ${i} ${Date.now()}`,
          }).then(() => create35(i + 1))
        }
        return create35(0)
      })
      .then(() => {
        cy.visit('/transactions')

        // Página 1: 30 filas, prev deshabilitado, next habilitado
        cy.get('main table tbody tr', { timeout: 15000 }).should('have.length', 30)
        cy.get('[data-testid="tx-pagination-info"]').should('contain', '35')
        cy.get('[data-testid="tx-pagination-prev"]').should('be.disabled')
        cy.get('[data-testid="tx-pagination-next"]').should('not.be.disabled')

        // Ir a página 2: 5 filas, prev habilitado, next deshabilitado
        cy.get('[data-testid="tx-pagination-next"]').click()
        cy.get('main table tbody tr', { timeout: 15000 }).should('have.length', 5)
        cy.get('[data-testid="tx-pagination-info"]').should('contain', 'Página 2 de 2')
        cy.get('[data-testid="tx-pagination-prev"]').should('not.be.disabled')
        cy.get('[data-testid="tx-pagination-next"]').should('be.disabled')

        // Volver a página 1
        cy.get('[data-testid="tx-pagination-prev"]').click()
        cy.get('main table tbody tr', { timeout: 15000 }).should('have.length', 30)
        cy.get('[data-testid="tx-pagination-info"]').should('contain', 'Página 1 de 2')
      })
  })
})