from users.models import User
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator


class Ingredient(models.Model):
    name = models.CharField(
        'Наименование ингридиента',
        max_length=100
    )
    izmerenie = models.CharField(
        'Единица измерения',
        max_length=15
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}'

class Tag(models.Model):
    name = models.CharField(
        'Название',
        null=False,
        unique=True,
        max_length=50,
    )
    color = models.CharField(
        'Цвет в HEX',
        max_length=7,
        null=False,
        unique=True,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Укажите цвет в формате HEX-кода.'
            )
        ]

    )
    slug = models.SlugField(
        verbose_name='Адрес для ссылки',
        max_length=25,
        unique=True,
        null=False,
        help_text='Уникальный адрес'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name}'


class Receipt(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        help_text='Укажите автора',
        on_delete=models.CASCADE,
        null=False,
    )
    title = models.CharField(
        verbose_name='Название рецепта',
        help_text='Укажите название блюда',
        null=False,
        max_length=150,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        help_text='Загрузите картинку ',
        upload_to='posts/',
        blank=False,
        null=False
    )
    text = models.TextField(
        verbose_name='Рецепт',
        help_text='Здесь будет Ваш рецепт',
        null=False,
        )

    ingridientes = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        help_text='Выберите ингридиенты',
        blank=False,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Выберите теги',
        blank=False,
    )
    tiempo = models.DecimalField(
        verbose_name='Время приготовления',
        help_text='Укажите время приготовления в минутах',
        null=False,
        max_digits=3,
        decimal_places=0,
        validators=[MinValueValidator(1)],
        )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.title} {self.author}'


class Quantity_ingredientes(models.Model):
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    quantity = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Количество ингредиентов для приготовления'
        verbose_name_plural = 'Количество ингредиентов для приготовления'
        constraints = [
            models.UniqueConstraint(
                fields=['receipt', 'ingredient'],
                name='unique_combination'
            )
        ]

    def __str__(self):
        return (f'{self.receipt.title}: '
                f'{self.ingredient.name} - '
                f'{self.quantity} '
                f'{self.ingredient.izmerenie}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user',
        verbose_name='Любимый автор',
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        verbose_name='Любимый рецепт',
        related_name='favorite_receipt',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'receipt'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.receipt.title}'


class For_shop(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_user',
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        verbose_name='В список покупок',
        related_name='shopping_receipt',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
    
    def __str__(self):
        return f'{self.user.username} - {self.receipt.title}'
