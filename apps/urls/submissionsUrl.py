from django.urls import path

from apps.views.submissionsView import SubmissionsView

urlpatterns = [
    path('', SubmissionsView.as_view()),
    path('<int:id>', SubmissionsView.as_view())
]
