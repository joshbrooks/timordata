
__author__ = 'josh'
from django.conf.urls import url
from geo import views

urlpatterns = [
    url(r'^index/', views.index, name='index'),
    url(r'^map/', views.map, name='map'),
    url(r'^placeenvelopes.json', views.placeenvelopes, name='placeenvelopes'),
    url(r'^places.json', views.places, name='places'),
    url(r'^placeconvexhulls/', views.placeconvexhulls, name='placeconvexhulls'),
    url(r'^projectplace/(?P<project_pk>\d+)/', views.projectplace, name='projectplace'),
    url(r'^search/(?P<model>\w+)/$', views.search, name="search"),
]
