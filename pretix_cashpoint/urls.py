from django.conf.urls import include, url

from . import views

cashpoint_api_patterns = [
    url(r'^orders/(?P<code>[^/]+)/cashpoint/', views.ApiCashpointView.as_view(),
        name='api.cashpoint'),
]

urlpatterns = [
    url(r'^api/v1/organizers/(?P<organizer>[^/]+)/events/(?P<event>[^/]+)/subevents/(?P<subevent>\d+)/',
        include(cashpoint_api_patterns)),
    url(r'^api/v1/organizers/(?P<organizer>[^/]+)/events/(?P<event>[^/]+)/',
        include(cashpoint_api_patterns)),
]
