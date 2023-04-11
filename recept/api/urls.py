from django.urls import include, path
from .views import UserTokenViewSet, UserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', UserTokenViewSet.as_view({'post': 'token'}), name='token'),
    #path('auth/token/logout/', UserDelTokenViewSet.as_view({'post': 'deltoken'}), name='deltoken'),
    path('auth/', include('djoser.urls.authtoken')),
]
