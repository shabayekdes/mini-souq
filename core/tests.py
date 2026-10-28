import json
import os
import re
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

# Prints the settings we care about as JSON; run in a fresh interpreter so each
# test controls the environment the settings module is imported with.
SETTINGS_PROBE = """
import json
import decouple
# Ignore any local .env file: only the environment passed in counts.
decouple.config = decouple.Config(decouple.RepositoryEmpty())
from core import settings as s
print(json.dumps({
    "DEBUG": s.DEBUG,
    "ALLOWED_HOSTS": s.ALLOWED_HOSTS,
    "CSRF_TRUSTED_ORIGINS": s.CSRF_TRUSTED_ORIGINS,
    "SECURE_SSL_REDIRECT": s.SECURE_SSL_REDIRECT,
    "SESSION_COOKIE_SECURE": s.SESSION_COOKIE_SECURE,
    "CSRF_COOKIE_SECURE": s.CSRF_COOKIE_SECURE,
    "SECURE_PROXY_SSL_HEADER": getattr(s, "SECURE_PROXY_SSL_HEADER", None),
    "DB_ENGINE": s.DATABASES["default"]["ENGINE"],
}))
"""

PROD_ENV = {
    "DJANGO_SECRET_KEY": "test-only-secret-key-not-used-anywhere-0123456789abcdef",
    "DATABASE_URL": "postgres://user:pass@db.example.invalid:5432/app",
}


def load_settings(**env):
    clean_env = {
        k: v for k, v in os.environ.items()
        if not k.startswith(("DJANGO_", "DATABASE_", "RAILWAY_"))
    }
    clean_env.update(env)
    return subprocess.run(
        [sys.executable, "-c", SETTINGS_PROBE],
        env=clean_env,
        cwd=settings.BASE_DIR,
        capture_output=True,
        text=True,
    )


class SettingsTests(SimpleTestCase):
    def test_production_requires_secret_key(self):
        result = load_settings(DATABASE_URL=PROD_ENV["DATABASE_URL"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)

    def test_production_requires_database_url(self):
        result = load_settings(DJANGO_SECRET_KEY=PROD_ENV["DJANGO_SECRET_KEY"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DATABASE_URL must be set", result.stderr)

    def test_database_url_password_not_leaked_on_bad_url(self):
        result = load_settings(
            DJANGO_SECRET_KEY=PROD_ENV["DJANGO_SECRET_KEY"],
            DATABASE_URL="nosuchdb://user:supersecretpw@host/db",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("supersecretpw", result.stderr)

    def test_debug_defaults_to_false_and_parses_strings(self):
        for value, expected in (("False", False), ("0", False), ("true", True), ("1", True)):
            result = load_settings(DJANGO_DEBUG=value, **PROD_ENV)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIs(json.loads(result.stdout)["DEBUG"], expected, value)
        result = load_settings(**PROD_ENV)
        self.assertIs(json.loads(result.stdout)["DEBUG"], False)

    def test_production_security_defaults(self):
        result = load_settings(RAILWAY_PUBLIC_DOMAIN="shop.up.railway.app", **PROD_ENV)
        self.assertEqual(result.returncode, 0, result.stderr)
        conf = json.loads(result.stdout)
        self.assertEqual(conf["ALLOWED_HOSTS"], ["shop.up.railway.app"])
        self.assertEqual(conf["CSRF_TRUSTED_ORIGINS"], ["https://shop.up.railway.app"])
        self.assertTrue(conf["SECURE_SSL_REDIRECT"])
        self.assertTrue(conf["SESSION_COOKIE_SECURE"])
        self.assertTrue(conf["CSRF_COOKIE_SECURE"])
        self.assertEqual(conf["SECURE_PROXY_SSL_HEADER"], ["HTTP_X_FORWARDED_PROTO", "https"])
        self.assertEqual(conf["DB_ENGINE"], "django.db.backends.postgresql")

    def test_explicit_hosts_from_env(self):
        result = load_settings(
            DJANGO_ALLOWED_HOSTS="shop.example.com, www.shop.example.com",
            DJANGO_CSRF_TRUSTED_ORIGINS="https://shop.example.com",
            **PROD_ENV,
        )
        conf = json.loads(result.stdout)
        self.assertEqual(conf["ALLOWED_HOSTS"], ["shop.example.com", "www.shop.example.com"])
        self.assertEqual(conf["CSRF_TRUSTED_ORIGINS"], ["https://shop.example.com"])

    def test_development_defaults(self):
        result = load_settings(DJANGO_DEBUG="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        conf = json.loads(result.stdout)
        self.assertEqual(conf["DB_ENGINE"], "django.db.backends.sqlite3")
        self.assertIn("localhost", conf["ALLOWED_HOSTS"])
        self.assertFalse(conf["SECURE_SSL_REDIRECT"])
        self.assertFalse(conf["SESSION_COOKIE_SECURE"])
        self.assertIsNone(conf["SECURE_PROXY_SSL_HEADER"])


class TemplateStaticPathTests(SimpleTestCase):
    def test_static_paths_have_no_leading_slash(self):
        # Regression: {% static '/demos/...' %} has no manifest entry, so every
        # page using the navbar returned 500 whenever DEBUG was off.
        offenders = [
            str(path.relative_to(settings.BASE_DIR))
            for path in (settings.BASE_DIR / "templates").rglob("*.html")
            if re.search(r"""\{%\s*static\s+['"]/""", path.read_text())
        ]
        self.assertEqual(offenders, [])


class AuthPagesTests(TestCase):
    """The allauth_ui slippers components must resolve (slippers.E001 is silenced)."""

    def test_login_and_signup_pages_render(self):
        for name in ('account_login', 'account_signup'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, 'csrfmiddlewaretoken')

    def test_logout_requires_post(self):
        # allauth's default (ACCOUNT_LOGOUT_ON_GET=False): a GET only shows a
        # confirmation page, so a cross-site link can't log users out.
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user('carol', 'carol@example.com', 'pw-carol-123!')
        self.client.force_login(user)
        self.client.get(reverse('account_logout'))
        self.assertEqual(self.client.get(reverse('cart_detail')).status_code, 200)

    def test_signup_creates_user_with_validated_password(self):
        from django.contrib.auth import get_user_model
        response = self.client.post(reverse('account_signup'), {
            'username': 'dave', 'email': 'dave@example.com',
            'password1': '123', 'password2': '123',
        })
        self.assertEqual(response.status_code, 200)  # re-rendered with errors
        self.assertFalse(get_user_model().objects.filter(username='dave').exists())
