import json

from django.test import TestCase, Client
from nhdb.models import Organization, OrganizationClass
from suggest.models import Suggest
from suggest.tests import create_suggestion, affirm
from suggest.tests import logger


def serialize_to_post(text):
    return serialize_dict_to_post(json.loads(text))


def serialize_dict_to_post(d):
    _d = {}
    for i in d:
        _d[i["name"]] = i["value"]
    return _d


# Create your tests here.
fundingoffer_test_data = (
    {"name": "csrfmiddlewaretoken", "value": "0dc9Yijn1WVElLGDW2DvT79ir0X9Gbtt"},
    {"name": "_method", "value": "POST"},
    {"name": "_url", "value": "/rest/donormapping/fundingoffer/"},
    {"name": "_action", "value": "CM"},
    {"name": "_description", "value": "Create a new funding offer in the database"},
    {"name": "_affected_instance_primary", "value": "donormapping_fundingoffer"},
    {"name": "__formtype", "value": "Create Form"},
    {"name": "_next", "value": "/suggest/#object=_suggestion_"},
    {"name": "title", "value": "My FundingOffer"},
    {"name": "organization", "value": "89"},
    {"name": "amount", "value": "131231"},
    {"name": "description", "value": "Hellow"},
    {"name": "sector", "value": "15"},
    {"name": "sector", "value": "20"},
    {"name": "sector", "value": "21"},
    {"name": "activity", "value": "2"},
    {"name": "activity", "value": "5"},
    {"name": "activity", "value": "8"},
    {"name": "beneficiary", "value": "40"},
    {"name": "beneficiary", "value": "45"},
    {"name": "_name", "value": "Josh"},
    {"name": "_email", "value": "josh.vdbroek@gmail.com"},
    {"name": "_comment", "value": ""},
)
document_data = (
    {"name": "csrfmiddlewaretoken", "value": "0dc9Yijn1WVElLGDW2DvT79ir0X9Gbtt"},
    {"name": "_method", "value": "POST"},
    {"name": "_url", "value": "/rest/donormapping/fundingofferdocument/"},
    {"name": "_action", "value": "CM"},
    {
        "name": "_description",
        "value": "Create a new funding offer document in the database",
    },
    {
        "name": "_affected_instance_primary",
        "value": "donormapping_fundingofferdocument",
    },
    {"name": "__formtype", "value": "Create Form"},
    {"name": "_next", "value": "/suggest/#object=_suggestion_"},
    {"name": "description", "value": "test"},
    {"name": "offer", "value": "_1_"},
    {"name": "_name", "value": "Josh"},
    {"name": "_email", "value": "josh.vdbroek@gmail.com"},
    {"name": "_comment", "value": ""},
)


class NewSuggestionTestCase(TestCase):

    fixtures = ["projectproperties.json"]

    # Submit a new Funding Offer

    def test_suggestion_update(self):
        """
        Make a suggestion and ensure that an UpdateSuggestionHelper is attached to the form
        :return:
        """
        c = Client()
        response = c.post(
            "/suggest/suggest/", serialize_dict_to_post(fundingoffer_test_data)
        )
        document = c.post("/suggest/suggest/", serialize_dict_to_post(document_data))
        assert int(response.status_code) == 201, (
            "Response code was %s" % response.status_code
        )
        assert int(document.status_code) == 201, (
            "Response code was %s" % response.status_code
        )


class SuggestDocumentTestCase(TestCase):
    """
    Load fixtures for a suggested FundingOffer and a Document
    """

    fixtures = ["projectproperties.json", "suggest_new_fundingoffer.json"]

    def test_children(self):
        """
        Check that our FundingOfferDocument is correctly identified as a "child" of suggestion for the FundingOffer
        :return:
        """
        orgtype = OrganizationClass(code="LNGO", orgtype="Local NGO")
        orgtype.save()
        Organization(pk=89, name="Belun", orgtype=orgtype).save()
        instance = Suggest.objects.get(
            affectedinstance__model_name="donormapping_fundingofferdocument"
        )
        related = Suggest.objects.get(
            affectedinstance__model_name="donormapping_fundingoffer"
        )
        references = instance.references()
        references_instances = [i[1] for i in references]
        try:
            ref = references_instances[0]
        except IndexError:
            logger.error("Index Error")
            logger.error("No references")
            logger.error(instance)
            logger.error(instance.data)
            raise

        assert ref == related
