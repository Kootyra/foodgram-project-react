from djoser.serializers import UserSerializer, serializers
from django.contrib.auth.password_validation import validate_password
from users.models import User, Follow
from receipt.models import (Ingredient, Receipt, Tag, Quantity_ingredientes,
                            Favorite, For_shop)
from django.core import exceptions as django_exceptions
from drf_extra_fields.fields import Base64ImageField
from rest_framework.validators import UniqueTogetherValidator


class CreateUserSerializer(UserSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_username(self, value):
        if value.lower() == "me":
            raise serializers.ValidationError("Username 'me' is not valid")
        return value


class ProfilesSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',)


class UserTokenSerializer(serializers.Serializer):
    class Meta:
        fields = ("email", "password", "token")
        model = User


class NewPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Wrong password.'}
            )
        if (validated_data['current_password']
           == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Change password'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'is_subscribed',
                  )

    def create(self, validated_data):
        author = self.context.get('author')
        user = self.context.get('request').user
        if author == user:
            raise serializers.ValidationError(
                {'error': 'Вы не можете подписаться на себя'}
            )
        if Follow.objects.filter(
            user=user,
            author=author
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Вы уже подписаны на этого автора'}
            )

        return Follow.objects.create(
            user=user,
            author=author
        )

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Follow.objects.filter(user=self.context['request'].user,
                                      author=obj).exists()
        )

    def get_receipt_count(self, obj):
        return obj.receipt.count()

    def get_receipts(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('receipts_limit')
        receipts = obj.receipt.all()
        if limit:
            receipts = receipts[:int(limit)]
        serializer = ReceiptSerializer(receipts, many=True, read_only=True)
        return serializer.data


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author',),
                message='У Вас уже есть подписка на этого автора'
            ),
        )

    def validate(self, data):
        if data.get('user') == data.get('author'):
            raise serializers.ValidationError(
                'Вы пытаетесь подписаться на себя')
        return data


class ReceiptSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Receipt
        fields = ('id', 'name',
                  'image', 'cooking_time')


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


class ReceiptReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReceiptIngredientSerializer(
        many=True, read_only=True, source='receipt')
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
                                        receipt=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and For_shop.objects.filter(
                user=self.context['request'].user,
                receipt=obj).exists()
        )


class ReceiptIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Ingredient
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

    def tags_and_ingredients_set(self, receipt, tags, ingredients):
        receipt.tags.set(tags)
        Ingredient.objects.bulk_create(
            [Ingredient(
                receipt=receipt,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        receipt = Receipt.objects.create(author=self.context['request'].user,
                                         **validated_data)
        self.tags_and_ingredients_set(receipt, tags, ingredients)
        return receipt

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        Receipt.objects.filter(
            receipt=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReceiptReadSerializer(instance,
                                     context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='receipt.id')
    name = serializers.ReadOnlyField(source='receipt.name')
    image = serializers.ImageField(source='receipt.image', required=False)
    cooking_time = serializers.IntegerField(
        source='receipt.cooking_time', required=False)

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
        receipt = self.context.get('receipt')
        if Favorite.objects.filter(
            user=user,
            receipt=receipt,
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в избранном'},
            )

        return Favorite.objects.create(user=user, receipt=receipt)


class ForShopSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='receipt.id')
    name = serializers.ReadOnlyField(source='receipt.name')
    image = serializers.ImageField(source='receipt.image', required=False)
    cooking_time = serializers.IntegerField(
        source='receipt.cooking_time', required=False)

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
        receipt = self.context.get('receipt')
        if For_shop.objects.filter(
            user=user,
            receipt=receipt,
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в избранном'},
            )

        return For_shop.objects.create(user=user, receipt=receipt)
