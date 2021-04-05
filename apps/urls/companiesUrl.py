from django.urls import path

from apps.views.companiesView import CompaniesView

urlpatterns = [
    path('', CompaniesView.as_view())
]
