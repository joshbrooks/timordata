from django.contrib import admin

# Register your models here.
from geo.models import AdminArea, World

admin.site.register(World)
admin.site.register(AdminArea)
