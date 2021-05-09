from django.urls import path

from apps.views.companiesViewOrm import CompaniesViewOrm

urlpatterns = [
    path('', CompaniesViewOrm.as_view())
]
