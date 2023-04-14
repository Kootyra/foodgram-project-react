from django.urls import include, path
from .views import (UserTokenViewSet, UserViewSet,
                    ReceptViewSet, TagViewSet,
                    IngredientViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', ReceptViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(
    r'ingredients', IngredientViewSet, basename='ingredients')
urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', UserTokenViewSet.as_view({'post': 'token'}),
         name='token'),
    path('auth/', include('djoser.urls.authtoken')),
]
