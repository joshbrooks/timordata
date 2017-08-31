import factory
from factory import DjangoModelFactory
from nhdb import models as nhdb


class ProjectStatusFactory(DjangoModelFactory):
    class Meta:
        model = nhdb.ProjectStatus

    code = factory.Faker('pystr', min_chars=2, max_chars=2)
    description = factory.Faker('sentence', nb_words=4)


class ProjectTypeFactory(DjangoModelFactory):
    class Meta:
        model = nhdb.ProjectType

    description = factory.Faker('sentence', nb_words=2)


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = nhdb.Project

    name = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('sentence', nb_words=20)
    startdate = factory.Faker('date')
    enddate = factory.Faker('date_object')
    verified = factory.Faker('date_object')
    notes = factory.Faker('sentence', nb_words=10)
    status = factory.RelatedFactory(ProjectStatusFactory)
    projecttype = factory.RelatedFactory(ProjectTypeFactory)
    stafffulltime = factory.Faker('pyint')
    staffparttime = factory.Faker('pyint')
