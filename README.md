# MiniSouq

![MiniSouq logo](logo.png)

MiniSouq is a small e-commerce storefront built with Django. Visitors can browse a product catalog by category and brand. Registered users can keep a shopping cart and place orders. Staff manage the catalog and view orders through the Django admin.

## Contents

- [Features](#features)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Local development](#local-development)
- [Configuration reference](#configuration-reference)
- [Database](#database)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Deploying to Railway](#deploying-to-railway)
- [Static and media files](#static-and-media-files)
- [Security notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

**Implemented**

- **Catalog:** home page with categories, brands and products; a shop page with category/brand filters, price sorting and pagination; product detail pages with related products.
- **Sale pricing:** products flagged as on sale are shown and charged at their sale price.
- **Accounts** (via [django-allauth](https://docs.allauth.org/)): sign up and log in with username or e-mail, log out, and reset a password by e-mail (requires SMTP). GitHub login is available once a GitHub OAuth app has been configured (see [GitHub login](#github-login)).
- **Cart** (logged-in users): add products with a quantity (1–99 per product), remove items, and see live totals. The navbar shows the number of items in the cart.
- **Checkout:** turns the cart into an `Order` with `OrderItem` rows. Totals and unit prices are always calculated on the server inside a database transaction.
- **Admin** (`/admin/`): manage categories, brands, products (with image uploads) and orders.

**Not implemented**

The template includes UI for these, but none of them have any functionality behind them:

- Payment processing. Orders are recorded but no payment is taken; the payment options on the checkout page are static text.
- Shipping/billing address forms, coupons, and stock/inventory tracking.
- Product search (the navbar search box doesn't submit anywhere yet), product reviews, and newsletter sign-up.
- Changing quantities from the cart page.
- Seller accounts or storefronts. Products are managed by staff in the admin.

## Technology stack

| Area | Choice |
| --- | --- |
| Language | Python 3.12+ (Docker/CI: 3.12) |
| Framework | Django 5.2 (LTS) |
| Auth | django-allauth 65 + django-allauth-ui |
| Database | PostgreSQL in production via `DATABASE_URL` (psycopg 3); SQLite for local development |
| Static files | WhiteNoise (compressed, hashed manifest) |
| App server | Gunicorn |
| Config | python-decouple (environment variables / `.env`) |
| Deployment | Docker image, deployed on Railway (`railway.toml`) |

Exact versions are pinned in [`requirements.txt`](requirements.txt).

## Project structure

```
core/         Project package: settings, root URLconf, WSGI/ASGI, settings tests
product/      Category, Brand and Product models; product detail view
store/        Home and shop (listing/filtering/pagination) views
checkout/     Cart, CartItem, Order, OrderItem; cart and checkout views;
              cart-count context processor
templates/    Site templates (layout, store, product, checkout, allauth overrides)
staticfiles/  Source static assets (theme CSS/JS/images), collected into local-cdn/
scripts/      Container start script (migrate + Gunicorn)
```

URL map:

| Path | View |
| --- | --- |
| `/` | Home |
| `/shop?category_id=&brand_id=&sort_by=price_asc\|price_desc&page=` | Shop listing |
| `/products/<id>/` | Product details |
| `/checkout/cart/` | Cart (login required) |
| `/checkout/add/<product_id>/` | Add to cart (POST, login required) |
| `/checkout/remove/<item_id>/` | Remove own cart item (POST, login required) |
| `/checkout/checkout/` | Checkout (login required) |
| `/checkout/order-success/` | Order confirmation (login required) |
| `/accounts/...` | django-allauth (login, signup, logout, password reset, GitHub) |
| `/admin/` | Django admin |

## Local development

### Prerequisites

- Python 3.12 or newer (tested on 3.12 and 3.14; the Docker image and CI use 3.12)
- Git
- PostgreSQL (optional; SQLite is used if `DATABASE_URL` is empty)

### Setup

```bash
git clone https://github.com/shabayekdes/mini-souq.git
cd mini-souq

python3 -m venv .venv               # check the version with: python3 --version
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # sets DJANGO_DEBUG=1 for local use
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. Add categories, brands and products at http://127.0.0.1:8000/admin/. Uploaded images go to `media/` and are served by `runserver` while `DJANGO_DEBUG=1`.

With `DJANGO_DEBUG=1` and no `DJANGO_SECRET_KEY`, a development-only key is used, and e-mails (e.g. password reset) are printed to the console.

## Configuration reference

All settings are read from environment variables, or from a local `.env` file, which is git-ignored. [`.env.example`](.env.example) lists every variable with comments.

**When `DJANGO_DEBUG` is unset or false, the app is in production mode.** In that mode `DJANGO_SECRET_KEY` and `DATABASE_URL` are required, and startup fails with `ImproperlyConfigured` if either is missing.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `0` | `1` for local development only. |
| `DJANGO_SECRET_KEY` | — (required in production) | Django secret key. Generate with `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`. |
| `DJANGO_ALLOWED_HOSTS` | empty | Comma-separated host names. `RAILWAY_PUBLIC_DOMAIN` is appended automatically; `localhost`/`127.0.0.1` are added in debug mode. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma-separated origins (`https://shop.example.com`). `https://$RAILWAY_PUBLIC_DOMAIN` is appended automatically. |
| `DATABASE_URL` | — (required in production) | e.g. `postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require`. Empty + debug → SQLite. |
| `DATABASE_SSL_REQUIRE` | `0` | Force `sslmode=require`. |
| `CONN_MAX_AGE` | `300` | Persistent DB connection lifetime in seconds (health-checked before reuse). |
| `DJANGO_SECURE_SSL_REDIRECT` | `1` in production | Redirect HTTP → HTTPS. |
| `DJANGO_SECURE_COOKIES` | `1` in production | `Secure` flag on session and CSRF cookies. |
| `DJANGO_TRUST_X_FORWARDED_PROTO` | `1` in production | Trust `X-Forwarded-Proto` from the TLS-terminating proxy. Only safe behind a proxy that sets it. |
| `DJANGO_SECURE_HSTS_SECONDS` | `0` | HSTS max-age. Opt-in (see [Security notes](#security-notes)). |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_SECURE_HSTS_PRELOAD` | `0` | HSTS flags. |
| `EMAIL_BACKEND` | console in debug, SMTP otherwise | Django e-mail backend. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | `smtp.gmail.com`, `587`, `1`, `0` | SMTP server. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | empty | SMTP credentials (use an app password). |
| `DEFAULT_FROM_EMAIL` | `EMAIL_HOST_USER` | Sender address for site and error e-mails. |
| `ADMIN_USER_NAME`, `ADMIN_USER_EMAIL` | `Admin user`, empty | Recipient of 500-error e-mails in production. |
| `ACCOUNT_EMAIL_VERIFICATION` | `none` | allauth: `none`, `optional` or `mandatory` (mandatory needs working SMTP). |
| `DJANGO_LOG_LEVEL` | `INFO` | Level for the `django` logger (logs go to stdout/stderr). |
| `PORT` | `8000` | Port Gunicorn binds to in the container. |
| `WEB_CONCURRENCY` | `1` | Gunicorn worker count. |
| `DJANGO_MIGRATE_ON_START` | `1` | Run `migrate` when the container starts. |

## Database

### SQLite (development)

If `DJANGO_DEBUG=1` and `DATABASE_URL` is empty, the project uses `db.sqlite3` in the repository root (git-ignored).

### PostgreSQL

Set `DATABASE_URL`:

```bash
DATABASE_URL=postgresql://minisouq:change-me@localhost:5432/minisouq
```

Hosted providers that require TLS (Neon, for example) should use `?sslmode=require` in the URL, or set `DATABASE_SSL_REQUIRE=1`. Never commit a real connection string. Keep it in `.env` locally and in the platform's variables in production.

A quick local PostgreSQL using Docker:

```bash
docker run --name minisouq-db -e POSTGRES_USER=minisouq -e POSTGRES_PASSWORD=change-me \
  -e POSTGRES_DB=minisouq -p 5432:5432 -d postgres:16
```

### Migrations

```bash
python manage.py migrate                          # apply
python manage.py showmigrations                   # status
python manage.py makemigrations --check --dry-run # verify models and migrations agree
```

Back up the production database before applying migrations to it.

### Administrator account

```bash
python manage.py createsuperuser
```

In the container: `docker exec -it <container> python manage.py createsuperuser`. On Railway, run the same command through the Railway CLI or shell.

## Running tests

The test suite uses Django's test runner and creates a temporary database (SQLite locally, PostgreSQL in CI). It never touches a configured production database, and no external services are needed.

```bash
DJANGO_DEBUG=1 python manage.py test
```

Run the same checks that CI runs:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
DJANGO_SECRET_KEY=dummy DATABASE_URL=sqlite:///:memory: DJANGO_ALLOWED_HOSTS=localhost \
  python manage.py check --deploy
```

`check --deploy` reports `security.W004` until HSTS is enabled. This is deliberate (see below).

## Docker

```bash
docker build -t minisouq .

docker run --rm -p 8000:8000 \
  -e DJANGO_SECRET_KEY='replace-with-a-generated-key' \
  -e DATABASE_URL='postgresql://minisouq:change-me@host.docker.internal:5432/minisouq' \
  -e DJANGO_ALLOWED_HOSTS=localhost \
  -e DJANGO_SECURE_SSL_REDIRECT=0 -e DJANGO_SECURE_COOKIES=0 \
  minisouq
```

The last two variables allow plain-HTTP access on `localhost`. Don't set them in production.

How the image works:

- It is based on `python:3.12-slim-bookworm` and installs dependencies into `/opt/venv`.
- Static files are collected at build time. No secrets are needed or stored in the image; a placeholder key exists only for that single build step.
- It runs as the unprivileged user `app`.
- `scripts/start.sh` runs `migrate` (unless `DJANGO_MIGRATE_ON_START=0`), then `exec`s Gunicorn so that it receives `SIGTERM` directly.
- `.dockerignore` keeps `.env`, `.git`, local databases and `media/` out of the build context.

## Deploying to Railway

`railway.toml` tells Railway to build the `Dockerfile`. Set these service variables in the Railway dashboard:

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | a newly generated secret |
| `DATABASE_URL` | reference the Railway PostgreSQL plugin variable, or your provider's URL |
| `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` | only for custom domains; the generated `*.up.railway.app` domain is picked up from `RAILWAY_PUBLIC_DOMAIN` |
| `ADMIN_USER_EMAIL`, `EMAIL_*` | optional, for error reports and password-reset e-mails |

Leave `DJANGO_DEBUG` unset (or `0`). Don't pass secrets as Docker build arguments.

Migrations run on every container start. That is fine for a single replica. If you scale to several replicas, set `DJANGO_MIGRATE_ON_START=0` and run `python manage.py migrate` once per deploy instead, for example as Railway's pre-deploy command. That stops replicas from racing to apply the same migration.

## Static and media files

- **Static files:** source assets live in `staticfiles/`. `collectstatic` gathers them into `local-cdn/` (git-ignored) at image build time, and WhiteNoise serves them with hashed file names and compression. Reference them in templates as `{% static 'path/file.css' %}`, with no leading slash, otherwise the manifest lookup fails when `DEBUG` is off.
- **Media (uploaded images):** saved under `media/` and served by Django **only when `DJANGO_DEBUG=1`**. In production, Django doesn't serve media, and a container's filesystem is wiped on every redeploy. For production, set up persistent object storage (e.g. S3-compatible storage via `django-storages`) or a mounted volume plus a web server for `/media/`. **This isn't configured yet, so product images uploaded in production won't be displayed.**

## Security notes

- **Secrets:** all secrets come from the environment. `.env` is git-ignored and `.env.example` contains placeholders only. If a secret is ever committed, treat it as compromised: rotate it with the provider first, then remove it from the repository and its history.
- **Production defaults:** `DEBUG` is off by default, and secure cookies, the HTTPS redirect, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: same-origin` are all on. Errors are logged to stdout and e-mailed to `ADMIN_USER_EMAIL` if it is set.
- **HSTS** is off until you opt in. Once HTTPS is confirmed on every domain, set `DJANGO_SECURE_HSTS_SECONDS=3600`, then raise it gradually (e.g. to `31536000`). Browsers cache it, so it can't be quickly undone.
- **Cart and checkout:** state-changing endpoints accept POST only and are CSRF-protected. Cart items are always looked up within the current user's cart. Prices and totals are computed on the server from the database; client-submitted totals are ignored.
- **Accounts:** allauth applies Django's password validators and rate-limits failed logins (in-process cache by default; configure a shared cache such as Redis if you run several workers or replicas). E-mail verification is `none` by default. Set `ACCOUNT_EMAIL_VERIFICATION=mandatory` once SMTP works.
- **Admin:** the admin is at `/admin/`. Give staff accounts strong, unique passwords.

### GitHub login

Create an OAuth app at https://github.com/settings/developers with the callback URL `https://<your-domain>/accounts/github/login/callback/`. Then add a *Social application* (provider: GitHub) with its client ID and secret in the Django admin. The credentials live in the database, not in source code.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ImproperlyConfigured: DJANGO_SECRET_KEY must be set...` | Set `DJANGO_SECRET_KEY`, or `DJANGO_DEBUG=1` for local work. |
| `ImproperlyConfigured: DATABASE_URL must be set...` | Set `DATABASE_URL`, or `DJANGO_DEBUG=1` to use SQLite locally. |
| `400 Bad Request` in production | The host isn't in `ALLOWED_HOSTS`. Add it to `DJANGO_ALLOWED_HOSTS`. |
| `403 CSRF verification failed` on a custom domain | Add `https://your-domain` to `DJANGO_CSRF_TRUSTED_ORIGINS`. |
| Redirect loop / "too many redirects" | The proxy isn't sending `X-Forwarded-Proto: https`. Fix the proxy, or set `DJANGO_SECURE_SSL_REDIRECT=0` if TLS is handled elsewhere. |
| Plain-HTTP local Docker run redirects to `https://localhost` | Set `DJANGO_SECURE_SSL_REDIRECT=0 DJANGO_SECURE_COOKIES=0` for local runs. |
| `ValueError: Missing staticfiles manifest entry` | Run `collectstatic`, and check the template uses `{% static %}` without a leading slash. |
| Product images 404 in production | Expected: media isn't served in production yet (see [Static and media files](#static-and-media-files)). |
| Password-reset e-mail never arrives | Configure the `EMAIL_*` variables. In debug mode, e-mails are printed to the console. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2024 Esmail Shabayek
