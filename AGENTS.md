# AGENTS.md

App de finanzas personales. Backend Django (DDD/clean architecture) + frontend React/Vite/TS + e2e Cypress, orquestados con Docker Compose.

## Estructura

- `backend/` — Django 5 + DRF + SimpleJWT. Proyecto Django en `config/`; feature modules en `modules/<feature>/` con capas `domain/`, `application/` (use cases, dtos, ports, result), `infrastructure/` (views, serializers, repositories, services, urls). Tests unitarios en `backend/tests/` usando fakes en memoria (`tests/fakes.py`), NO tocan DB.
- `frontend/` — React 19 + Vite + TypeScript + Tailwind v4 + shadcn (estilo `radix-nova`). Alias `@` → `src/`. Rutas en `src/routes.tsx`. API client en `src/lib/api.ts` (prefija `/api`, el proxy de Vite lo reenvía a `backend:8000`).
- `cypress/` — suite e2e independiente con su propio `package.json`. `baseUrl` y puertos se toman del `.env` local (ver abajo).
- `data/` — CSV de ejemplo, no código.

## Setup y entorno

- `.env` (raíz) define puertos y credenciales. **Está gitignorado**: se usa `docker-compose.yml` (también gitignorado) que lee de ahí. `docker-compose.example.yml` + `.env.example` son las plantillas.
- Los puertos locales no son los defaults: el `.env` usa `FRONTEND_PORT=36130` y `BACKEND_PORT=36131`. Cypress apunta a `http://localhost:36130`. Si cambiás el `.env`, Cypress se rompe salvo que actualices `cypress/cypress.config.ts`.
- Levantar todo: `docker compose up --build`. El backend corre `migrate` y luego `runserver 0.0.0.0:8000` dentro del contenedor.
- Migraciones: se generan y aplican dentro del contenedor `finance_backend`. No hay Makefile ni script wrapper: usá `docker compose exec backend python manage.py makemigrations` / `migrate`.
- Mensajes de error del backend están en español (i18n, `LANGUAGE_CODE='es'`, traducciones en `backend/locale/es`). Los tests activan `translation.activate("es")` para validar mensajes.

## Comandos útiles

Todo corre vía Docker. Desde la raíz:

```bash
docker compose up --build              # levanta db + backend + frontend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py test                      # todos los tests
docker compose exec backend python manage.py test tests.auths.application.use_cases.test_login_user
docker compose exec backend python manage.py test tests.auths.application.use_cases.test_login_user.TestLoginUserUseCase.test_returns_tokens_for_valid_credentials
```

Frontend (lint/build; no hay test unitarios de frontend):

```bash
docker compose exec frontend npm run lint          # eslint
docker compose exec frontend npm run lint:fix
docker compose exec frontend npm run build         # tsc -b && vite build (typecheck incluido)
```

Cypress (requiere backend y frontend levantados en los puertos del `.env`):

```bash
cd cypress && npm run test:e2e          # headless
cd cypress && npm run cy:open           # interactivo
cd cypress && npx cypress run --spec e2e/auth.cy.ts   # un solo spec
```

## Convenciones que se rompen si no las sabés

- **Arquitectura del backend**: las vistas en `infrastructure/views.py` delegan a use cases en `application/use_cases/`. Los use cases reciben dependencias por constructor (repository, token_service) y devuelven un `Result` con `is_success`, `value`, `errors`. No devolver dicts sueltos ni lanzar excepciones de dominio desde las vistas; usar el `Result`.
- Los repositorios de infraestructura (`DjangoUserRepository`) implementan los ports definidos en `domain/repositories.py` y `application/ports.py`. Para agregar un feature nuevo, seguís el mismo split de capas.
- **Tests unitarios del backend**: no usan pytest ni fixtures de Django. Son `unittest.TestCase` con fakes en `tests/fakes.py` (`InMemoryUserRepository`, `FakeTokenService`). Nuevos tests de use cases van en `tests/<feature>/application/use_cases/` y consumen esos fakes.
- `AUTH_USER_MODEL = 'auths.User'` (custom, login por email, sin `username`). El app label es `auths` pero el módulo es `modules.auths`.
- El cliente HTTP del frontend (`src/lib/api.ts`) hace refresh automático de JWT en 401 y guarda tokens en `localStorage` bajo las claves `pf.access` / `pf.refresh`. Los tests e2e de Cypress setean/limpian esas mismas claves (`cypress/support/commands.ts`).
- shadcn: componentes en `frontend/src/components/ui/`. Config en `frontend/components.json` con estilo `radix-nova` y alias `@/components`, `@/lib`, `@/hooks`. Agregar componentes con `npx shadcn add <name>` desde `frontend/`.

## Antes de entregar

- Backend: `docker compose exec backend python manage.py test`
- Frontend: `docker compose exec frontend npm run lint && docker compose exec frontend npm run build`
- E2E (si tocás flujos de UI): `cd cypress && npm run test:e2e`