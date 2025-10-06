# core/search/urls.py
# URL configuration for search API

from django.urls import path
from .views import SearchView, AutocompleteView, SearchHealthView

app_name = 'search'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
    path('health/', SearchHealthView.as_view(), name='health'),
]
