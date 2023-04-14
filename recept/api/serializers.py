from djoser.serializers import UserSerializer, serializers
from django.contrib.auth.password_validation import validate_password
from users.models import User, Follow
from foodgram.models import Ingredient, Recept, Tag, Quantity_ingredientes, Favorite, For_shop
from django.core import exceptions as django_exceptions
from drf_extra_fields.fields import Base64ImageField




class NewUserSerializer(UserSerializer):
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')
    
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

    
    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Follow.objects.filter(user=self.context['request'].user,
                                      author=obj).exists()
        )


class ReceptSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    tiempo = serializers.ReadOnlyField()

    class Meta:
        model = Recept
        fields = ('id', 'title',
                  'image', 'tiempo')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ReceptIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = Quantity_ingredientes
        fields = ('id', 'name',
                  'izmerenie', 'quantity')


class ReceptReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReceptIngredientSerializer(
        many=True, read_only=True, source='recept')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recept
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'title', 'image',
                  'text', 'tiempo')

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


class ReceptIngredientCreateSerializer(serializers.ModelSerializer):
    """Ингредиент и количество для создания рецепта."""
    id = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'quantity')


class ReceptCreateSerializer(serializers.ModelSerializer):
    """[POST, PATCH, DELETE] Создание, изменение и удаление рецепта."""
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    ingredients = ReceptIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recept
        fields = ('id', 'ingredients',
                  'tags', 'image',
                  'title', 'text',
                  'tiempo', 'author')
        extra_kwargs = {
            'ingredients': {'required': True, 'allow_blank': False},
            'tags': {'required': True, 'allow_blank': False},
            'title': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'image': {'required': True, 'allow_blank': False},
            'tiempo': {'required': True},
        }

    def validate(self, obj):
        for field in ['title', 'text', 'tiempo']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field} - Это обязательное поле.'
                )
        if not obj.get('tags'):
            raise serializers.ValidationError(
                'Выбирите не менее одного тега'
            )
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Выбирите не менее одного ингридиента'
            )
        inrgedient_id_list = [item['id'] for item in obj.get('ingredients')]
        unique_ingredient_id_list = set(inrgedient_id_list)
        if len(inrgedient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Вы уже добавили данный ингридиент'
            )
        return obj

    def tags_and_ingredients_set(self, recept, tags, ingredients):
        recept.tags.set(tags)
        Ingredient.objects.bulk_create(
            [Ingredient(
                recept=recept,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['quantity']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recept.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.title = validated_data.get('title', instance.title)
        instance.text = validated_data.get('text', instance.text)
        instance.tiempo = validated_data.get(
            'tiempo', instance.tiempo)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        Recept.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReceptReadSerializer(instance,
                                    context=self.context).data
