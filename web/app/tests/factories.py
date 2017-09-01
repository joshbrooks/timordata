import factory
from django.core.files.uploadedfile import SimpleUploadedFile
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


class OrganizationClassFactory(DjangoModelFactory):
    class Meta:
        model = nhdb.OrganizationClass

    code = factory.Faker('pystr', min_chars=2, max_chars=4)
    orgtype = factory.Faker('sentence', nb_words=4)


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = nhdb.Organization

    name = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('sentence', nb_words=4)
    orgtype = OrganizationClassFactory()
    active = factory.Faker('pybool')
    fongtilid = factory.Faker('pyint')
    justiceid = factory.Faker('pyint')
    stafffulltime =factory.Faker('pyint')
    staffparttime = factory.Faker('pyint')
    verified = factory.Faker('date_object')
    phoneprimary = factory.Faker('pystr', min_chars=10, max_chars=10)
    phonesecondary =factory.Faker('pystr', min_chars=10, max_chars=10)
    email = factory.Faker('pystr', min_chars=10, max_chars=10)
    fax = factory.Faker('pystr', min_chars=10, max_chars=10)
    web = factory.Faker('pystr', min_chars=10, max_chars=10)
    facebook = factory.Faker('pystr', min_chars=10, max_chars=10)


class ProjectImageFactory(DjangoModelFactory):
    class Meta:
        model = nhdb.ProjectImage

    description = factory.Faker('sentence', nb_words=4)
    image = SimpleUploadedFile('best_file_eva.txt', b'these are the file contents!')
    project = ProjectFactory()
