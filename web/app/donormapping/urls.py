from django.conf.urls import include, url
from donormapping import views

fundingoffer = [
    url(r'^$', views.fundingofferlist, name="list"),
    #url(r'^$', views.FundingOfferList.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/$', views.FundingOfferDetail.as_view(), name="detail"),
    url(r'^(?P<pk>[0-9]+)/ajax/$', views.FundingOfferDetail.as_view(template_name='donormapping/fundingoffer_detail_ajax.html'),
        name='ajax'),
    url(r'^new/$', views.FundingOfferCreate.as_view(), name="create"),
]

survey = [
    url(r'^$', views.FundingSurveyList.as_view(), name="list"),
    url(r'^new/$', views.FundingSurveyCreate.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/$', views.FundingSurveyDetail.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/edit/$', views.FundingSurveyEdit.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/delete/$', views.FundingSurveyDelete.as_view(), name="delete"),
]

urlpatterns = [
    url(r'^survey/', include(survey, namespace='survey')),
    url(r'^fundingoffer/', include(fundingoffer, namespace='fundingoffer')),
    url(r'^$', views.index, name="index"),
    url(r'^donors/$', views.DonorSurveyResponseView.as_view()),
    url(r'^form/(?P<model>\w+)/(?P<form>\w+)', views.form, name="form"),

]
