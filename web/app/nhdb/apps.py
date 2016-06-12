from django.apps import AppConfig

class NhdbAppConfig(AppConfig):

    name = 'nhdb'
    verbose_name = 'nhdb'

    def ready(self):

        import nhdb.signals
