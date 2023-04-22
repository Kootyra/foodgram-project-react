from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = 'admin'
    USER = 'user'
    ROLES = [
        (ADMIN, 'Administrator'),
        (USER, 'User'),
    ]

    email = models.EmailField(
        verbose_name='Email',
        max_length=254,
        unique=True
    )
    username = models.CharField(
        verbose_name='Логин',
        max_length=150,
        null=False,
        unique=True
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=10,
        choices=ROLES,
        default=USER
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        null=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        null=False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = (
            models.UniqueConstraint(
                fields=('username', 'email'),
                name='unique_login_fields'
            ),
        )

    def __str__(self) -> str:
        return f'{self.username}: {self.email}'


class Subscriptions(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='subscriber'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
