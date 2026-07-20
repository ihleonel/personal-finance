import './commands';

before(() => {
  cy.fixture('users').then((users: Record<string, { email: string; password: string; first_name?: string; last_name?: string }>) => {
    const entries = Object.entries(users)
    for (const [, u] of entries) {
      cy.request({
        method: 'POST',
        url: '/api/auth/register/',
        body: {
          email: u.email,
          password: u.password,
          first_name: u.first_name ?? '',
          last_name: u.last_name ?? '',
        },
        failOnStatusCode: false,
      })
    }
  })
})