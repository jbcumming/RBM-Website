from django.conf.urls import patterns, include, url
from rbm_website.apps.users import views

# The URLs for the user objects
urlpatterns = patterns('',
    url(r'^(?P<username>\w+)/$', views.view_user, name='view_user'),
)
