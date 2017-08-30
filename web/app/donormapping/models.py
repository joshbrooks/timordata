import re

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
# from ckeditor.fields import RichTextField

from datetime import datetime
from pivottable import pivot_table

def isRichField(test):
    """
    Check to see if there's HTML tags in the code or if it's just text
    :return:
    """
    ultimate_regexp = "(?i)<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?>"
    if re.search(ultimate_regexp, test):
        return True
    return False

class FundingOffer(models.Model):
    def __unicode__(self):

        return self.title

    def get_absolute_url(self):
        return reverse('donormapping:fundingoffer:detail', kwargs={'pk': self.pk})

    title = models.CharField(max_length=256, help_text="Put in the title")
    #description = RichTextField(config_name='awesome_ckeditor')
    description = models.TextField()
    summary = models.TextField(null=True, blank=True)
    organization = models.ForeignKey('nhdb.Organization')
    amount = models.IntegerField(null=True)

    conditions = models.TextField(null=True, blank=True)

    application_end_date = models.DateField(null=True, blank=True)
    district = models.ManyToManyField('geo.District', blank=True)
    all_districts = models.BooleanField(default=False)

    sector = models.ManyToManyField(
        'nhdb.PropertyTag', blank=True, related_name="fundingoffer_sector", limit_choices_to={'path__startswith':"INV."})
    activity = models.ManyToManyField(
        'nhdb.PropertyTag', blank=True, related_name="fundingoffer_activity", limit_choices_to={'path__startswith':"ACT."})
    beneficiary = models.ManyToManyField(
        'nhdb.PropertyTag',  blank=True, related_name="fundingoffer_beneficiary", limit_choices_to={'path__startswith':"BEN."})


    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

    @property
    def rich_description(self):
        return isRichField(self.description)    \

    @property
    def rich_summary(self):
        return isRichField(self.summary)


class FundingOfferDocument(models.Model):
    offer = models.ForeignKey(FundingOffer)
    file = models.FileField(upload_to="publications", max_length=256, null=True, blank=True)
    description = models.CharField(max_length=128)


class DonorAnnouncement(models.Model):
    '''
    Information about announcements made about donor funding concerning Timor Leste
    '''

    def __unicode__(self):
        return self.title

    date = models.DateField()
    source = models.ForeignKey('nhdb.Organization', blank=True, null=True)
    title = models.CharField(max_length=256)
    summary = models.TextField()
    content = models.TextField()



class DonorSurveyResponse(models.Model):
    '''
    A response received from an organization to Belun's "Funding Opportunities Form".
    Records the survey response - even if "no information" - so that we have a record of who Belun has requested
    information from
    '''

    @property
    def organization_display(self):
        if self.organization:
            return self.organization.__unicode__()
        else:
            return self.organizationname

    def __unicode__(self):
        return '{} - {} - {}'.format(self.organization_display, self.survey_date, self.get_response_display())

    OPTION_RESPONSE = (
        ('ND', 'No (works directly with local partners)'),
        ('NO', 'No (does not provide funding)'),
        ('Y', 'Funding is available'),
        ('L', 'Funding is not yet available'),
        ('W', 'Awaiting a response'),
    )
    organization = models.ForeignKey('nhdb.Organization', null=True, blank=True)
    organizationname = models.TextField(null=True, blank=True)
    survey_date = models.DateField(default=datetime.today)
    response_date = models.DateField(null=True, blank=True)
    response = models.CharField(max_length=2, choices=OPTION_RESPONSE)


class FundingSurveyInfoMethods(models.Model):
    """
    Describes how donor organisations or recipients search for
    partner organisations
    """

    def __unicode__(self):
        return self.description

    description = models.CharField(max_length=200)

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))


class FundingSurvey(models.Model):
    """
    This is a one-off table to collect information
    about funding opportunities in TimorLeste
    """
    def __unicode__(self):
        return '{}'.format(self.organizationname)

    def get_absolute_url(self):
        return reverse('donormapping:survey:detail', kwargs={'pk': self.pk})

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

    STATEMENTS = (
        (1, 'Strongly Disagree'),
        (2, 'Disagree'),
        (3, 'Neutral'),
        (4, 'Agree'),
        (5, 'Strongly Agree'),
    )

    FREQUENCIES = (
        ('D', 'Every Day'),
        ('W', 'Once per week'),
        ('F', 'Once per 2 weeks (fortnightly)'),
        ('M', 'Once per month'),
        ('N', 'Less than once per month (or never)')
    )

    # Idea: Search for an existing organization to populate this?
    organizationname = models.CharField(max_length=100)
    organizationtype = models.ForeignKey('nhdb.OrganizationClass', verbose_name =_("Organization type"))
    properties = models.ManyToManyField('nhdb.PropertyTag',
                                        limit_choices_to={'path__startswith': 'INV.'}, verbose_name = _("Properties"))
    fundinggiven = models.NullBooleanField(default=None, verbose_name=_("Has your organization given funding in the past year?"))
    fundinggiveamt = models.IntegerField(null=True, blank=True,
                                         verbose_name=_("How much (approximately) given in the past year?"))

    fundingreceived = models.NullBooleanField(default=None, verbose_name=_("Has your organization received funding in the past year?"))
    fundingrecvamt = models.IntegerField(null=True, blank=True,
                                         verbose_name=_("How much (approximately) received in the past year?"))

    # Free answer (text) questions about finding donors or organisations
    # to fund (how do you find...?)
    fundinggiverel = models.ManyToManyField(FundingSurveyInfoMethods, blank=True, related_name="fundinggiverel",
                                            verbose_name=_("How do you find your recipients?"))
    fundinggivemethod = models.CharField(max_length=128, blank=True, verbose_name=_("If other, please write:"))

    fundingrecvrel = models.ManyToManyField(FundingSurveyInfoMethods, blank=True, related_name="fundingrecvrel",
                                            verbose_name=_("How do you find your donors?"))
    fundingrecvmethod = models.CharField(max_length=128, null=True, blank=True, verbose_name=_("If other, please write:"),
                                         help_text=_("e.g. Television Advertising, Radio, Newspapers"))

    # These questions are to find out how different organisations
    # feel about issues that they face
    qfunding = models.IntegerField(null=True, blank=True, verbose_name=_("Donor funding is difficult to find"),
                                   choices=STATEMENTS)
    qrecipients = models.IntegerField(null=True, blank=True, verbose_name=_("Recipient organisations are hard to find"),
                                      choices=STATEMENTS)
    qtransport = models.IntegerField(null=True, blank=True,
                                     verbose_name=_("Receiving funds is difficult because of transport problems"),
                                     choices=STATEMENTS)
    qprocess = models.IntegerField(null=True, blank=True,
                                   verbose_name=_("Applying for funds is very difficult because the process is complicated"),
                                   choices=STATEMENTS)
    qdonorsector = models.IntegerField(null=True, blank=True,
                                       verbose_name=_("Donor funding is hard to find for the sectors this organization works in"),
                                       choices=STATEMENTS)

    # These questions are to find out how technology is used in the 
    # different organisations
    usefacebook = models.CharField(verbose_name=_("How often do you use Facebook?"), max_length=2, choices=FREQUENCIES)
    usegmail = models.CharField(verbose_name=_("How often do you use Gmail?"), max_length=2, choices=FREQUENCIES)
    usegoogle = models.CharField(verbose_name=_("How often do you use Google Search?"), max_length=2, choices=FREQUENCIES)

    # These questions are to find out what technology access organisations have
    hascomputer = models.BooleanField(default=False, verbose_name=_("I have access to a computer"))
    hasprinter = models.BooleanField(default=False, verbose_name=_("I have access to a printer"))
    hasmobile = models.BooleanField(default=False, verbose_name=_("I have access to a basic mobile phone (calls and SMS) at work"))
    hassmartphone = models.BooleanField(default=False, verbose_name=_("I have access to a smartphone or tablet (with internet access)"))
