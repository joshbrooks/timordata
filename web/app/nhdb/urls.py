from django.conf.urls import url, include

from belun import views_authentication
from nhdb import views, views_excel

organization = [
    # url(r'^$', views.OrganizationList.as_view(), name='list'),
    url(r'^$', views.organizationlist, name='list'),
    url(r'^xls$', views_excel.organization, name='list_as_excel'),
    url(r'^list.json/$', views.organization_list_as_json, name='list_as_json'),
    url(r'^(?P<pk>[0-9]+)/$', views.OrganizationDetail.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/ajax/$', views.OrganizationDetail.as_view(template_name='nhdb/organization_detail_ajax.html'),
        name='detail_ajax'),
    url(r'^new/$', views.OrganizationCreate.as_view(), name='create'),
    url(r'^form/(?P<form>\w+)/$', views.organizationupdate, name='update'),
    url(r'^(?P<pk>\d+)/delete/$', views.OrganizationDelete.as_view(), name='delete'),
    url(r'^(?P<pk>\d+)/description_(?P<language_code>\w+)/$', views.organizationdescription, name='update_description'),
    # url(r'^(?P<pk>\d+)/places/$', views.organizationplace, name='places'),
    url(r'^(?P<organization_id>\d+)/people/$', views.organization_persons, name='persons'),
]

propertytag = [
    url(r'^$', views.PropertyTagList.as_view(), name='list'),
    url(r'^select', views.propertytagselect, name='select'),
]

projectperson = [
    url(r'^new/', views.newprojectperson, name='create'),
    url(r'^$', views.ProjectPersonList.as_view(), name='list'),
    url(r'(?P<pk>[0-9]+)/$', views.ProjectPersonDetail.as_view(), name='detail'),
    url(r'(?P<pk>[0-9]+)/delete/$', views.ProjectPersonDelete.as_view(template_name='nhdb/projectperson_delete.html'),
        name='detail'),
]

project = [

    # url(r'^$', views.ProjectList.as_view(), name='list'),
    url(r'^$', views.projectlist, name='list'),
    # url(r'^table/$', views.ProjectList.as_view(template_name='nhdb/project_list_table.html'), name='list_as_table'),
    url(r'^places/$', views.projectplaces, name='places'),
    url(r'^xls$', views_excel.project, name='list_as_excel'),
    url(r'^csv/$', views.projectcsv, name='csv'),
    url(r'^csv_export/$', views.projectcsv_nutrition, name='csv_export'),

    # url(r'^new/$', views.project_suggested, name="new"),

    # url(r'^form/(?P<form>\w+)/$', views.projectupdate), Replaced with new URL scheme

    url(r'^confirm/(?P<suggest_pk>[0-9]+)/$', views.confirmprojectchange, name='confirm'),
    url(r'(?P<pk>[0-9]+)/$', views.ProjectDetail.as_view(), name='detail'),
    url(r'(?P<pk>[0-9]+)/organizations/$', views.ProjectOrganizations.as_view(), name='projectorganizations'),
    url(r'^(?P<pk>[0-9]+)/ajax/$', views.ProjectDetail.as_view(template_name='nhdb/project_detail_ajax.html'),
        name='project_detail_ajax'),
    url(r'^(?P<pk>[0-9]+)/update/description/(?P<language_code>\w+)/$', views.projectdescription),
    url(r'^thumbnail_image/', views.thumbnail_image, name='thumbnail_image'),
    url(r'^verification/', views.project_verification, name='verification'),
]
person = [
    url(r'^$', views.PersonList.as_view(), name='list'),
    url(r'(?P<pk>[0-9]+)/$', views.PersonDetail.as_view(), name='detail'),
    url(r'(?P<pk>[0-9]+)/ajax/$', views.PersonDetail.as_view(template_name='nhdb/person_detail_ajax.html'),
        name='detail_ajax'),
    url(r'new/$', views.PersonCreate.as_view(template_name='nhdb/person_create.html'), name='new'),
]

projectorganization = [
    url(r'^$', views.ProjectOrganizationList.as_view(), name="list"),
    # url(r'(?P<pk>[0-9]+)/$', views.ProjectOrganizationDetail.as_view(), name='detail'),
    url(r'new/', views.newprojectorganization, name='create'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.ProjectOrganizationDelete.as_view()),
]

urlpatterns = [
    url(r'^organization/', include(organization, namespace='organization')),
    # url(r'^organizationplace/(?P<pk>[0-9]+)/$', views.organizationplace, name="organizationplace"),
    url(r'^projectimage/(?P<pk>[0-9]+)/$', views.ProjectImageDetail.as_view()),
    url(r'^projectimage/(?P<pk>[0-9]+)/delete/$', views.ProjectImageDelete.as_view()),
    url(r'^projectimage/new/$', views.projectimagecreate),
    url(r'^project/', include(project, namespace='project')),
    url(r'^person/', include(person, namespace='person')),
    url(r'^form/(?P<model>\w+)/(?P<form>\w+)/$', views.form, name="form"),
    url(r'^form/(?P<model>\w+)/$', views.form),
    url(r'^projectperson/', include(projectperson, namespace='projectperson')),
    url(r'^projectorganization/', include(projectorganization, namespace='projectorganization')),
    url(r'^projectproperties/', views.projectproperties, name="projectproperties"),
    url(r'^personproject/', views.PersonProjectList.as_view(), name="personproject"),
    url(r'^propertytag/', include(propertytag, namespace='propertytag')),
    url(r'^logout/$', views_authentication.logmeout, name='logout'),
    url(r'^login/$', views_authentication.logmein, name="login"),
    url(r'^search/(?P<model>\w+)/$', views.search, name="search"),
    url(r'^index/', views.index, name='index'),
    url(r'^partners/', views.partners, name='partners'),
    url(r'^downloadexcel/$', views.downloadexcel, name='downloadexcel'),
    url(r'^downloadexcel/list/', views.ExcelDownloadFeedbackList.as_view(), name='downloadexcel_list'),

    url(r'^lookup_tables/', views.lookup_tables, name='lookup_tables'),
]
