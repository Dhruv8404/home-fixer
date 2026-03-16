from django.urls import re_path
from .consumers import BookingTrackingConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/booking/(?P<booking_id>\d+)/$',
        BookingTrackingConsumer.as_asgi()
    ),
]