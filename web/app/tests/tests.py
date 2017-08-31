from django.test import TestCase
from nhdb import models as nhdb
from .factories import ProjectFactory, ProjectStatusFactory, ProjectTypeFactory

class ProjectTestCase(TestCase):
    def setUp(self):
        ProjectFactory(pk = 1)

    def test_create_project(self):
        """Project created and updated times work correctly"""
        project = nhdb.Project.objects.get(pk=1)
        self.assertEqual(project.created_at, project.updated_at)

    def test_update_project(self):
        """Project created and updated times work correctly"""
        project = nhdb.Project.objects.get(pk=1)
        project.description = 'foofoobarbar'
        project.save(force_updated_at=True)
        project.refresh_from_db()
        self.assertNotEqual(project.created_at, project.updated_at)

    def test_delete_project(self):
        """Project delete time works correctly"""
        project = nhdb.Project.objects.get(pk=1)
        project.delete()
        project.refresh_from_db()
        self.assertIsNotNone(project.deleted_at)