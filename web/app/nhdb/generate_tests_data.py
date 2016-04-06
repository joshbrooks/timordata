from django.core import serializers

from nhdb.models import Project, PropertyTag

with open('/webapps/project/belun/nhdb/fixtures/project_100.json', 'w') as f:
    f.write(serializers.serialize('json', Project.objects.all()[:100]
    ))

with open('/webapps/project/belun/nhdb/fixtures/projectproperties.json', 'w') as f:
    f.write(serializers.serialize('json', PropertyTag.objects.all()
    ))
