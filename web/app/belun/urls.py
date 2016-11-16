from donormapping import urls as dm_urls
from geo import urls as geo_urls
from library import urls as library_urls
from suggest import rest_urls as suggest_rest_urls
from nhdb import rest_urls as nhdb_rest_urls
from library import rest_urls as library_rest_urls
from donormapping import rest_urls as donormapping_rest_urls
from rest_framework_swagger import urls as rest_framework_swagger_urls
from suggest import urls as suggest_urls

from django.conf.urls import include, url
from django.contrib import admin
from belun import views
from nhdb import urls as nhdb_urls
from belun. views import selecttwo, chosen, selecttwo_create
from belun.flatpage_trans import flatpage_translation
from library.views import thumbnail as th
from django.conf import settings
from django.contrib.auth import views as auth_views
admin.autodiscover()

urlpatterns = [

    url(r'^accounts/login/$', auth_views.login),
    url(r'^accounts/logout/$', auth_views.logout),
    url(r'^login/$', auth_views.login, name="login"),
    url(r'^logout/', auth_views.logout, name='logout'),
    url(r'^flatpages/flatpages/$', views.flatpagelist, name='flatpage'),
    url(r'^flatpage/(?P<pk>[0-9]+)$', views.FlatpageDetail.as_view(), name='flatpage'),

    # url(r'^index/$', views.index, name='index'),
    # url(r'^about/$', views.about, name='about'),
    # url(r'^history/$', views.history, name='history'),
    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/', include(admin.site.urls), name="admin"),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    # url(r'^logout/', logmeout, name='logout'),

    url(r'^nhdb/', include(nhdb_urls, namespace='nhdb')),

    url(r'^geo/', include(geo_urls, namespace='geo')),
    url(r'^suggest/', include(suggest_urls, namespace='suggest')),

    # url(r'^datatrans/', include(datatrans_urls)),

    url(r'^library/', include(library_urls, namespace="library")),

    url(r'^donormapping/', include(dm_urls, namespace="donormapping")),

    url(r'^rest/nhdb/', include(nhdb_rest_urls, namespace="nhdb_rest")),
    url(r'^rest/suggest/', include(suggest_rest_urls)),
    url(r'^rest/library/', include(library_rest_urls)),
    url(r'^rest/donormapping/', include(donormapping_rest_urls)),

    url(r'^docs/', include(rest_framework_swagger_urls)),

    url(r'^selecttwo/$', selecttwo),
    url(r'^selecttwo/(?P<app_name>[a-z]+)/(?P<model_name>[a-z]+)/(?P<filter_field>[a-z]+)/(?P<filter_param>[a-z]+)/', selecttwo),
    url(r'^chosen/(?P<app_name>[a-z]+)/(?P<model_name>[a-z]+)/(?P<filter_field>[a-z]+)/(?P<filter_param>[a-z]+)/', chosen),
    url(r'^selecttwo_create/(?P<app_name>[a-z]+)/(?P<model_name>[a-z]+)/(?P<filter_field>[a-z]+)/(?P<filter_param>[a-z]+)/', selecttwo_create),
    url(r'^thumbnail/(?P<app_name>[a-z]+)/(?P<model_name>[a-z]+)/(?P<pk>[0-9]+).jpg', th),
    url(r'^thumbnail/(?P<app_name>[a-z]+)/(?P<model_name>[a-z]+)/(?P<pk>[0-9]+)/(?P<res>[0-9]+).jpg', th),


    url(r'^$', views.index, name='home'),
    url(r'^indexmanifest/$', views.indexmanifest, name='indexmanifest'),
    url(r'^page/(?P<url>.*)$', flatpage_translation, name='django.contrib.flatpages.views.flatpage'),
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += url(r'^__debug__/', include(debug_toolbar.urls))
