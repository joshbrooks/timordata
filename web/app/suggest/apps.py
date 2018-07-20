from django.apps import AppConfig


class SuggestAppConfig(AppConfig):

    name = "suggest"
    verbose_name = "Suggestions"

    def ready(self):

        import signals
