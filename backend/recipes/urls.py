from django.urls import path

from api.views import recipe_redirect

urlpatterns = [
    path('s/<int:pk>/', recipe_redirect, name='short-link')
]
