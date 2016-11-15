from django.conf.urls import url, include
from library import views


publication = [
    # url(r'^$', views.PublicationList.as_view(), name='list'),
    # url(r'^$', views.PublicationList.as_view(), name='list'),
    url(r'^$', views.publicationlist, name='list'),

    url(r'^xls/$', views.project_table_excel, name='list_as_excel'),

    url(r'^(?P<pk>[0-9]+)/$', views.PublicationDetail.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/ajax/$', views.PublicationDetail.as_view(), name='detail-ajax'),
    url(r'^suggested_publication/$', views.suggested_publications),
    url(r'^suggested_publication/(?P<suggestion_pk>[0-9]+)/$', views.suggested_publication),

    url(r'^(?P<pk>\d+)/delete/$', views.PublicationDelete.as_view(), name='delete'),
    url(r'^dashboard/$', views.publicationdashboard),
]

version = [
    url(r'^$', views.VersionList.as_view(), name='list'),
    url(r'^thumbnail/(?P<version_pk>\d+)/(?P<language>\w+)$', views.version_thumbnail, name='thumbnail'),
    # url(r'(?P<pk>[0-9]+)/$', views.VersionDetail.as_view(), name='detail'),
    url(r'(?P<pk>[0-9]+)/edit/$', views.VersionUpdate.as_view(), name='edit'),
    url(r'^(?P<pk>\d+)/delete/$', views.VersionDelete.as_view(), name='delete'),


    # NGINX thumbnail not found: Redirects to library view
    url(r'^thumbnail_nginx/$',
        views.version_thumbnail_nginx, name='nginx_thumbnail'),

    url(r'^(?P<pk>[0-9]+)/page/(?P<page>\d+)/(?P<language>\w+)$', views.version_page, name='s'),
]

untl = [
    url(r'^$', views.publicationlist, name='list'),
]


urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^publication/', include(publication, namespace='publication')),
    url(r'^untl/', include(untl, namespace='untl')),
    url(r'^version/', include(version, namespace='version')),
    url(r'^form/(?P<model>\w+)/$', views.form, name="form"),
    url(r'^form/(?P<model>\w+)/(?P<form>\w+)/$', views.form, name="form")
]
