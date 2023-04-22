from django.contrib import admin

from . import models


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'measurement_unit')
    list_filter = ('name', )
    search_fields = ('name', )


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


@admin.register(models.Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'cooking_time', 'text',
                    'image', 'author', 'in_favorites')
    list_editable = (
        'name', 'cooking_time', 'text',
        'image', 'author'
    )
    readonly_fields = ('in_favorites',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorite_recipe.count()


@admin.register(models.Quantity_ingredientes)
class QuantityIngredientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'recipe', 'ingredient', 'amount')
    list_editable = ('recipe', 'ingredient', 'amount')


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(models.For_shop)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'recipe')
    list_editable = ('user', 'recipe')
