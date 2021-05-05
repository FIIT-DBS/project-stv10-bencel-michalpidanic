from django.urls import path

from apps.views.submissionsViewOrm import SubmissionsViewOrm

urlpatterns = [
    path('', SubmissionsViewOrm.as_view()),
    path('<int:id>', SubmissionsViewOrm.as_view())
]
