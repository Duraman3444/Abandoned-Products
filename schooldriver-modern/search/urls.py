from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.global_search_view, name='global_search'),
    path('api/suggestions/', views.search_suggestions_api, name='suggestions_api'),
    path('api/save/', views.save_search, name='save_search'),
    path('api/saved/<int:search_id>/delete/', views.delete_saved_search, name='delete_saved_search'),
    path('saved/<int:search_id>/', views.load_saved_search, name='load_saved_search'),
]
