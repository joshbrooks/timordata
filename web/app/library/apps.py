from django.apps import AppConfig


class LibraryAppConfig(AppConfig):

    name = 'library'
    verbose_name = 'Library'

    def ready(self):

        import library.signals
