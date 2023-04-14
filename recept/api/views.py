from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets, filters, mixins
from rest_framework.decorators import action
from users.models import User, Follow
from foodgram.models import Ingredient, Recept, Tag, Favorite, For_shop
from .serializers import (FollowSerializer, ReceptSerializer,
                          IngredientSerializer, TagSerializer,
                          ReceptCreateSerializer, NewPasswordSerializer,
                          ReceptReadSerializer, NewUserSerializer,
                          ProfilesSerializer, UserTokenSerializer)
from .permissions import AdminOrUser, IsAuthorOrReadOnly
from rest_framework_simplejwt.tokens import AccessToken
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ReceptFilter

FILE = 'shop.txt'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfilesSerializer
        return NewUserSerializer

    def get_permissions(self):
        self.permission_classes = [permissions.AllowAny]
        if self.request.method == "GET":
            self.permission_classes = [AdminOrUser]
        return super(UserViewSet, self).get_permissions()

    @action(
        methods=[
            "get",
            "post",
        ],
        detail=False,
    )
    def profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == "POST":
            serializer = NewUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        serializer = ProfilesSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['post'],
            permission_classes=(permissions.IsAuthenticated,))
    def set_password(self, request):
        serializer = NewPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'New password save'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get', ],
            permission_classes=(permissions.IsAuthenticated,),
            )
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = FollowSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Follow, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Вы отписались от пользователя'},
                            status=status.HTTP_204_NO_CONTENT)


class UserTokenViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def token(self, request):
        serializer = UserTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_form = serializer.initial_data.get('email')
        user_form_pas = serializer.initial_data.get('password')
        user = get_object_or_404(User, email=user_form, password=user_form_pas)
        token = AccessToken.for_user(user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (permissions.AllowAny, )
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class ReceptViewSet(viewsets.ModelViewSet):
    queryset = Recept.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = ReceptFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReceptReadSerializer
        return ReceptCreateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recept = get_object_or_404(Recept, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = ReceptSerializer(recept, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(user=request.user,
                                           recept=recept).exists():
                Favorite.objects.create(user=request.user, recept=recept)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт ранее добавлен в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              recept=recept).delete()
            return Response({'detail': 'Рецепт удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recept = get_object_or_404(Recept, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = ReceptSerializer(recept, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not For_shop.objects.filter(user=request.user,
                                           recept=recept).exists():
                For_shop.objects.create(user=request.user, recept=recept)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(For_shop, user=request.user,
                              recept=recept).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            Ingredient.objects
            .filter(recept__shopping_recept__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('quantity'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__izmerenie')
        )
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
                            content_type='text/plain')
        file['Content-Disposition'] = (f'attachment; filename={FILE}')
        return file
