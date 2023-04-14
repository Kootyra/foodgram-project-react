from django.contrib import admin

from . import models


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'izmerenie')
    list_filter = ('name', )
    search_fields = ('name', )


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


@admin.register(models.Recept)
class ReceptAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'tiempo', 'text',
                    'image', 'author', 'in_favorites')
    list_editable = (
        'title', 'tiempo', 'text',
        'image', 'author'
    )
    readonly_fields = ('in_favorites',)
    list_filter = ('title', 'author', 'tags')
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorite_recept.count()


@admin.register(models.Quantity_ingredientes)
class QuantityIngredientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'recept', 'ingredient', 'quantity')
    list_editable = ('recept', 'ingredient', 'quantity')


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'recept')
    list_editable = ('user', 'recept')


@admin.register(models.For_shop)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'recept')
    list_editable = ('user', 'recept')
