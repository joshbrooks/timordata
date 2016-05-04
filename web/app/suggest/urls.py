__author__ = 'josh'

from django.conf.urls import patterns, url, include
from suggest import views


urlpatterns = [

    # url(r'^$', views.SuggestList.as_view(), name='list'),
    url(r'^$', views.suggestlist, name='list'),
    url(r'^(?P<pk>[0-9]+)/$', views.suggest, name='detail'),
    url(r'^(?P<pk>[0-9]+)/ajax/$', views.suggest_ajax, name='detail_ajax'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.suggestdelete, name='delete'),

    url(r'^hide/(?P<model_name>[a-z_]+)/(?P<model_pk>[0-9]+)/(?P<state>[A-Z]+)/', views.hide),

    url(r'^hide/(?P<model_name>[a-z_]+)/(?P<model_pk>[0-9]+)/', views.hide),

    url(r'^unhide/(?P<model_name>[a-z_]+)/(?P<model_pk>[0-9]+)/(?P<state>[A-Z]+)/', views.unhide),

    url(r'^unhide/(?P<model_name>[a-z_]+)/(?P<model_pk>[0-9]+)/', views.unhide),


    url(r'^create/$', views.SuggestCreate.as_view(), name='create'),

    url(r'^suggest/$', views.suggestcreate, name='suggest'),

    url(r'^(?P<model_name>[a-z_]+)/(?P<model_pk>[0-9]+)/$', views.suggestlist, name='suggest_model'),
    url(r'^(?P<model_name>[a-z_]+)/$', views.suggestlist, name='suggest_model_name'),

    ]