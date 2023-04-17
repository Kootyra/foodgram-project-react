from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets, filters, mixins
from rest_framework.decorators import action
from users.models import User, Follow
from receipt.models import Ingredient, Receipt, Tag, Favorite, For_shop
from .serializers import (FollowSerializer,
                          IngredientSerializer, TagSerializer,
                          ReceiptCreateSerializer, NewPasswordSerializer,
                          ReceiptReadSerializer, CreateUserSerializer,
                          ProfilesSerializer, UserTokenSerializer,
                          Quantity_ingredientes, FavoriteSerializer,
                          ForShopSerializer)
from .permissions import AdminOrUser, IsAuthorOrReadOnly
from rest_framework_simplejwt.tokens import AccessToken
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ReceiptFilter

FILE = 'shop.txt'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfilesSerializer
        return CreateUserSerializer

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
            serializer = CreateUserSerializer(data=request.data)
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
        authors = self.paginate_queryset(
            Follow.objects.filter(user=request.user)
        )
        serializer = FollowSerializer(
            authors,
            many=True,
            context={
                    'request': request,
                    'subscriptions':
                    set(Follow.objects.filter(user_id=self.request.user)
                        .values_list('author_id', flat=True))
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = FollowSerializer(
                context={
                    'author': author,
                    'request': request,
                    'subscriptions':
                    set(Follow.objects.filter(user_id=self.request.user)
                        .values_list('author_id', flat=True))
                }, data=request.data
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            get_object_or_404(Follow, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Вы отписались от пользователя'},
                            status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        context = super(UserViewSet, self).get_serializer_context()
        return context


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


class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = ReceiptFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReceiptReadSerializer
        return ReceiptCreateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, **kwargs):
        receipt = get_object_or_404(Receipt, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            data = {'user': user.id, 'receipt': receipt.id}
            serializer = FavoriteSerializer(context={
                'receipt': receipt,
                'request': request
            }, data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт ранее добавлен в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              receipt=receipt).delete()
            return Response({'detail': 'Рецепт удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        receipt = get_object_or_404(Receipt, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            data = {'user': user.id, 'receipt': receipt.id}
            serializer = ForShopSerializer(context={
                'receipt': receipt,
                'request': request
            }, data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт ранее добавлен в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(For_shop, user=request.user,
                              receipt=receipt).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            Quantity_ingredientes.objects
            .filter(receipt__shopping_receipt__user=request.user)
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
