from django.contrib.auth.views import LogoutView
from django.urls import path

app_name = 'users'

urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
]
