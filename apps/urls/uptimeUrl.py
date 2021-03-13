from django.urls import path

from apps.views.uptimeView import UptimeView

urlpatterns = [
    path('', UptimeView.getHealth),
]
