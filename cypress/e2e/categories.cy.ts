describe('Categorías', () => {
  const CATEGORY_NAME = `Categoría Cypress ${Date.now()}`
  let accessToken: string | null = null

  function deactivateAllActiveCategories() {
    if (!accessToken) return cy.wrap(null)
    return cy
      .request({
        method: 'GET',
        url: '/api/categories/',
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then((res) => {
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

  function createCategoryViaApi(input: { name: string; kind: string }) {
    return cy.request({
      method: 'POST',
      url: '/api/categories/',
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
    deactivateAllActiveCategories()
  })

  it('visitar /categories sin auth redirige a /login', () => {
    cy.clearAuth()
    cy.visit('/categories')
    cy.url().should('include', '/login')
  })

  it('muestra la página de categorías sin categorías activas', () => {
    deactivateAllActiveCategories().then(() => {
      cy.visit('/categories')
      cy.contains('h1', 'Categorías').should('be.visible')
      cy.contains('button', 'Nueva categoría').should('be.visible')
      cy.get('main').contains('Activo').should('not.exist')
    })
  })

  it('crea una categoría y aparece en la lista', () => {
    deactivateAllActiveCategories().then(() => {
      cy.visit('/categories')
      cy.contains('button', 'Nueva categoría').click()
      cy.get('[role=dialog]').should('be.visible')
      cy.get('input[name="name"]').type(CATEGORY_NAME)

      cy.get('[data-testid="category-kind-select"]').click()
      cy.get('[role=option]').contains('Ingreso').click()

      cy.get('[role=dialog]').contains('button', 'Crear categoría').click()

      cy.contains(CATEGORY_NAME, { timeout: 10000 }).should('be.visible')
      cy.contains('Ingreso').should('be.visible')
      cy.contains('Activo').should('be.visible')
    })
  })

  it('valida que el nombre sea obligatorio', () => {
    deactivateAllActiveCategories().then(() => {
      cy.visit('/categories')
      cy.contains('button', 'Nueva categoría').click()
      cy.get('[role=dialog]').should('be.visible')
      cy.get('[role=dialog]').contains('button', 'Crear categoría').click()
      cy.contains('El nombre de la categoría es obligatorio').should('be.visible')
    })
  })

  it('rechaza nombre duplicado para categoría activa', () => {
    deactivateAllActiveCategories().then(() => {
      createCategoryViaApi({ name: CATEGORY_NAME, kind: 'expense' }).then(() => {
        cy.visit('/categories')
        cy.contains(CATEGORY_NAME, { timeout: 10000 }).should('be.visible')
        cy.contains('button', 'Nueva categoría').click()
        cy.get('[role=dialog]').should('be.visible')
        cy.get('input[name="name"]').type(CATEGORY_NAME)
        cy.get('[data-testid="category-kind-select"]').click()
        cy.get('[role=option]').contains('Egreso').click()
        cy.get('[role=dialog]').contains('button', 'Crear categoría').click()
        cy.get('[role=alert]', { timeout: 10000 }).should('be.visible')
        cy.contains('[role=alert]', /ya tenés una categoría activa con ese nombre/i).should('be.visible')
      })
    })
  })

  it('edita el nombre de una categoría', () => {
    deactivateAllActiveCategories().then(() => {
      createCategoryViaApi({ name: CATEGORY_NAME, kind: 'income' }).then(() => {
        cy.visit('/categories')
        cy.contains(CATEGORY_NAME, { timeout: 10000 }).should('be.visible')

        cy.get(`button[aria-label="Editar ${CATEGORY_NAME}"]`).first().click()
        cy.get('[role=dialog]').should('be.visible')
        cy.get('input[name="name"]').clear().type('Categoría Editada')
        cy.get('[role=dialog]').contains('button', 'Guardar cambios').click()

        cy.contains('Categoría Editada', { timeout: 10000 }).should('be.visible')
      })
    })
  })

  it('desactiva una categoría y refleja el estado', () => {
    deactivateAllActiveCategories().then(() => {
      createCategoryViaApi({ name: CATEGORY_NAME, kind: 'expense' }).then(() => {
        cy.visit('/categories')
        cy.contains(CATEGORY_NAME, { timeout: 10000 }).should('be.visible')
        cy.contains('Activo').should('be.visible')

        cy.get(`button[aria-label="Desactivar ${CATEGORY_NAME}"]`).first().click()
        cy.contains('button', 'Sí').click()

        cy.contains('Inactivo', { timeout: 10000 }).should('be.visible')
      })
    })
  })

  it('activa una categoría inactiva y refleja el estado', () => {
    deactivateAllActiveCategories().then(() => {
      createCategoryViaApi({ name: CATEGORY_NAME, kind: 'income' }).then((res) => {
        const categoryId = res.body.id
        cy.request({
          method: 'POST',
          url: `/api/categories/${categoryId}/deactivate/`,
          headers: { Authorization: `Bearer ${accessToken}` },
        }).then(() => {
          cy.visit('/categories')
          cy.contains(CATEGORY_NAME, { timeout: 10000 }).should('be.visible')
          cy.contains('Inactivo').should('be.visible')

          cy.get(`button[aria-label="Activar ${CATEGORY_NAME}"]`).first().click()
          cy.contains('button', 'Sí').click()

          cy.contains('Activo', { timeout: 10000 }).should('be.visible')
        })
      })
    })
  })
})