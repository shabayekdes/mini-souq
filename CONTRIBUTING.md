# Contributing to MiniSouq

## Workflow

1. Create a branch from `main`.
2. Make focused changes and add or update tests for them.
3. Run the checks below locally. CI (`.github/workflows/ci.yml`) runs the same checks against PostgreSQL and also builds the Docker image.
4. Open a pull request describing what changed and why.

```bash
DJANGO_DEBUG=1 python manage.py check
DJANGO_DEBUG=1 python manage.py makemigrations --check --dry-run
DJANGO_DEBUG=1 python manage.py test
```

## Project conventions

- **Never commit secrets.** No real keys, passwords or connection strings in code, docs, tests, fixtures or commit messages. Use environment variables and the placeholders in `.env.example`. If you commit one by accident, tell the maintainer straight away so it can be rotated; deleting it in a later commit is not enough.
- **New settings** go in `core/settings.py`, read through `decouple.config(...)` with a safe production default. Document each one in `.env.example` and in the README configuration table.
- **Money and authorization stay on the server.** Compute prices and totals from the database (`Product.current_price`). Scope user-owned objects to `request.user`, e.g. `get_object_or_404(CartItem, id=..., cart__user=request.user)`. Never trust IDs, prices or totals from the request.
- **State-changing views** must be POST-only (`@require_POST`) and their templates must include `{% csrf_token %}`.
- **Forms** list editable fields explicitly (`fields = [...]`), never `exclude`.
- **Migrations:** commit the migrations generated for any model change. Avoid destructive operations (dropping columns or tables, or narrowing a type that could fail on existing rows) without discussing them first. Production data must survive.
- **Templates:** use `{% static 'path' %}` without a leading slash, and don't use `|safe` on user- or admin-supplied content.
- **Dependencies** are pinned in `requirements.txt`. Upgrade them deliberately (Dependabot opens PRs) and re-run the tests. Django stays on the current LTS line.
