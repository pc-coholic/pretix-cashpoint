from django.apps import AppConfig


class PluginApp(AppConfig):
    name = 'pretix_cashpoint'
    verbose_name = 'Pretix Cashpoint API'

    class PretixPluginMeta:
        name = 'Pretix Cashpoint API'
        author = 'Martin Gross'
        description = 'Pretix Cashpoint API plugin'
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_cashpoint.PluginApp'
