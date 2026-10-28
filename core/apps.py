from django.contrib.staticfiles.apps import StaticFilesConfig


class CoreStaticFilesConfig(StaticFilesConfig):
    # django-allauth-ui ships its Tailwind *source* file. Its `@import "tailwindcss"`
    # can't be resolved by the manifest storage and breaks collectstatic; the
    # templates only use the compiled allauth_ui/output.css.
    ignore_patterns = StaticFilesConfig.ignore_patterns + ["allauth_ui/input.css"]
