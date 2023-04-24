from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets, filters, mixins
from rest_framework.decorators import action
from users.models import User, Subscriptions
from receipt.models import Ingredient, Receipt, Tag, Favorite, For_shop
from .serializers import (SubscribeSerializer,
                          IngredientSerializer, TagSerializer,
                          ReceiptCreateSerializer,
                          ReceiptReadSerializer,
                          Quantity_ingredientes, FavoriteSerializer,
                          ForShopSerializer, UserSubscribeSerializer,
                          CustomUserCreateSerializer, CustomPasswordSerializer,
                          CustomUserSerializer, )
from .permissions import IsAuthorOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ReceiptFilter
from djoser.views import UserViewSet
from .mixins import ListSubscriptionViewSet
from .paginators import PageLimitPagination

FILE = 'shop.txt'


class CustomUserViewSet(UserViewSet):
    add_serializer = UserSubscribeSerializer
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        if self.action == 'set_password':
            return CustomPasswordSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = (permissions.IsAuthenticated,)
        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request,
                        'subscriptions':
                        set(Subscriptions.objects
                            .filter(user_id=self.request.user)
                            .values_list('author_id', flat=True))})
        return context

    @action(
        methods=('post', 'delete',),
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        serializer = SubscribeSerializer(
            data={'user': user.id,
                  'author': author.id, },
            context=self.get_serializer_context()
        )
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer_show = UserSubscribeSerializer(
                author,
                context={'recipes_limit': request.GET.get('recipes_limit')})
            return Response(serializer_show.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription = Subscriptions.objects.filter(
                user=user,
                author=author
            )
            subscription.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(ListSubscriptionViewSet):
    serializer_class = UserSubscribeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageLimitPagination

    def get_queryset(self):
        return User.objects.filter(subscription__user=self.request.user)


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
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = ReceiptFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReceiptReadSerializer
        return ReceiptCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request,
                        "favorite": Favorite.objects
                        .filter(user_id=self.request.user)
                        .values_list('recipe_id', flat=True),
                        "shopping_cart": For_shop.objects
                        .filter(user_id=self.request.user)
                        .values_list('recipe_id', flat=True)})
        return context


    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Receipt, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(context={
                 'recipe': recipe,
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
                              recipe=recipe).delete()
            return Response({'detail': 'Рецепт удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Receipt, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = ForShopSerializer(context={
                 'recipe': recipe,
                 'request': request
             }, data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт ранее добавлен в корзину'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(For_shop, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            Quantity_ingredientes.objects
            .filter(recipe__shopping_recipe__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__measurement_unit')
        )
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
                            content_type='text/plain')
        file['Content-Disposition'] = (f'attachment; filename={FILE}')
        return file

