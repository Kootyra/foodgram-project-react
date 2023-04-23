from djoser.serializers import (PasswordSerializer, UserCreateSerializer,
                                UserSerializer, serializers)
from users.models import User, Subscriptions
from receipt.models import (Ingredient, Receipt, Tag, Quantity_ingredientes,
                            Favorite, For_shop)
from drf_extra_fields.fields import Base64ImageField
from rest_framework.validators import UniqueTogetherValidator


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.subscriber.filter(author=obj).exists())


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class CustomPasswordSerializer(PasswordSerializer):
    current_password = serializers.CharField(required=True)


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Receipt
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribeSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count',)
        read_only_fields = ('email', 'username', 'first_name', 'last_name',)

    def get_is_subscribed(*args):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request is not None:
            limit = request.GET.get('recipes_limit')
        else:
            limit = self.context.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriptions
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=('user', 'author',),
                message='Автор уже в Ваших подписках'
            ),
        )

    def validate(self, data):
        if data.get('user') == data.get('author'):
            raise serializers.ValidationError(
                'Вы пытаетесь подписаться на себя')
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ReceiptIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = Quantity_ingredientes
        fields = ('id', 'name',
                  'measurement_unit', 'amount')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.subscriber.filter(author=obj).exists())


class ReceiptReadSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReceiptIngredientSerializer(
        many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Receipt
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and For_shop.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )


class ReceiptIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Quantity_ingredientes
        fields = ('id', 'amount')


class ReceiptCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    ingredients = ReceiptIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Receipt
        fields = ('id', 'ingredients',
                  'tags', 'image',
                  'name', 'text',
                  'cooking_time', 'author')
        extra_kwargs = {
            'ingredients': {'required': True, 'allow_blank': False},
            'tags': {'required': True, 'allow_blank': False},
            'name': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'image': {'required': True, 'allow_blank': False},
            'cooking_time': {'required': True},
        }

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field} - Это обязательное поле.'
                )
        if not obj.get('tags'):
            raise serializers.ValidationError(
                'Выбeрите не менее одного тега'
            )
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Выбeрите не менее одного ингридиента'
            )
        inrgedient_id_list = [item['id'] for item in obj.get('ingredients')]
        unique_ingredient_id_list = set(inrgedient_id_list)
        if len(inrgedient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Вы уже добавили данный ингрeдиент'
            )
        return obj

    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        Quantity_ingredientes.objects.bulk_create(
            [Quantity_ingredientes(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Receipt.objects.create(author=self.context['request'].user,
                                        **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        Quantity_ingredientes.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReceiptReadSerializer(instance,
                                     context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', required=False)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', required=False)

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = self.context.get('recipe')
        if Favorite.objects.filter(
            user=user,
            recipe=recipe,
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в избранном'},
            )

        return Favorite.objects.create(user=user, recipe=recipe)


class ForShopSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', required=False)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', required=False)

    class Meta:
        model = For_shop
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = self.context.get('recipe')
        if For_shop.objects.filter(
            user=user,
            recipe=recipe,
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в избранном'},
            )

        return For_shop.objects.create(user=user, recipe=recipe)
