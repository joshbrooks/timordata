from django.contrib.gis import geos
from django.test import TestCase
import unittest
from mp_lite import MP_Lite
from geo.models import AdminArea as Place
from test_data import wkt_data, wkt_envelope

# Test geometry (actually Aileu suco I think?)
r = geos.WKTReader()
g = r.read(wkt_data)

envelope_reader = geos.WKTReader()
envelope = r.read(wkt_envelope)


class PathMethodTests(TestCase):

    # fixtures = ['adminarea.json']

    def setUp(self):

        self.TestDistrict = Place.objects.create(
            pcode=1, name="Aileu", path="AIL", geom=g, envelope=envelope
        )
        self.TestSubDistrict = Place.objects.create(
            pcode=101, name="Aileu", path="AIL.AIL", geom=g, envelope=envelope
        )
        self.TestSuco = Place.objects.create(
            pcode=10101, name="Aileu", path="AIL.AIL.AIL", geom=g, envelope=envelope
        )

        Place.objects.create(
            pcode=2, name="Covalima", path="COV", geom=g, envelope=envelope
        )
        Place.objects.create(
            pcode=201, name="Covalima", path="COV.COV", geom=g, envelope=envelope
        )
        Place.objects.create(
            pcode=20101, name="Covalima", path="COV.COV.COV", geom=g, envelope=envelope
        )

    def test_can_create_parent_node(self):
        """
        Create a simple parent node
        """

        self.assertEqual(Place.get_root_nodes().count(), 2)

    def test_add_child(self):
        """
        Add a child node
        """
        try:
            p = Place.objects.get(pk=1)
            p.delete()
        except Place.DoesNotExist:
            pass

        pa = Place(pcode=1, name="Aileu", path="AIL", geom=g, envelope=envelope)
        pa.save()

        p = Place(
            pcode=101, name="Aileu sub", path="AIL.AIL", geom=g, envelope=envelope
        )
        p.save()

        self.assertEqual(pa.get_children()[0], p)

        p.delete()

    @unittest.expectedFailure
    def test_needparent(self):
        """
        This test tries to add a suco to a sudistrict which does not exist
        """
        p = Place(
            pcode=20101,
            name="Fail this suco",
            path="AIN.AIL.AIL",
            geom=g,
            envelope=envelope,
        )
        p.save()

    def test_delete_parent_and_child(self):
        """
        Delete 'COV' and its descendants
        """
        p = Place.objects.get(pk=2)
        self.assertEqual(p.get_descendants(include_self=False).count(), 2)
        self.assertEqual(p.get_descendants(include_self=True).count(), 3)

        p.delete()
        self.assertEqual(
            Place.objects.extra(where=["path LIKE %s"], params=["COV%"]).count(), 0
        )

    def test_move_to(self):
        """
        Create a new top level 'AAA' and move 'AIL.AIL' to this new place.
        
        - Test that 'AIL' now has 0 descendants
        - Test that 'AIL.AIL.AIL' -> 'AAA.AIL.AIL'
        """
        p = Place(pcode=20101, name="New suco", path="AAA", geom=g, envelope=envelope)
        p.save()

        moveplace = Place.objects.get(path="AIL.AIL")
        moveplace.move(p)

        self.assertEqual(
            Place.objects.extra(where=["path LIKE %s"], params=["AIL.%"]).count(), 0
        )

        self.assertEqual(
            Place.objects.extra(where=["path = %s"], params=["AAA.AIL"]).count(), 1
        )

        self.assertEqual(
            Place.objects.extra(where=["path = %s"], params=["AAA.AIL.AIL"]).count(), 1
        )

        self.assertEqual(
            Place.objects.extra(where=["path = %s"], params=["AIL.AIL.AIL"]).count(), 0
        )
