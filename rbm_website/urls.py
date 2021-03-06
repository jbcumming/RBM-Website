from django.conf.urls import patterns, include, url
from django.contrib import admin

# The Django Admin URLs
admin.autodiscover()

# All the URLs available to the application
urlpatterns = patterns('',
    url(r'^$', 'rbm_website.views.home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^faq/$', 'rbm_website.views.faq', name='faq'),
    url(r'^rbm/', include('rbm_website.apps.rbm.urls')),
    url(r'^users/', include('rbm_website.apps.users.urls')),
    url(r'^accounts/logout/', 'rbm_website.apps.users.views.user_logout'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'users/login.html'}),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^tutorial/$', 'rbm_website.views.tutorial', name='tutorial')
)
