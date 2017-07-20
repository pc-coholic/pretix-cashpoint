from django.apps import AppConfig


class PluginApp(AppConfig):
    name = 'pretix_cashpoint'
    verbose_name = 'Pretix Cashpoint API'

    class PretixPluginMeta:
        name = 'Pretix Cashpoint API plugin'
        author = 'Martin Gross'
        description = 'pretix plugin that implements an API endpoint to mark orders as paid.'
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_cashpoint.PluginApp'
