from django.contrib import admin
from django.contrib.auth import get_user_model

from recipes.models import (
    Ingredient, Favorite, Recipe, ShoppingCart, Subscription, Tag
)

User = get_user_model()

admin.site.empty_value_display = 'Не задано'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ класс для управления пользователями."""

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
    )
    list_display_links = ('username',)
    search_fields = ('username', 'email',)
    ordering = ('username',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ класс для управления тегами."""

    list_display = ('name', 'slug',)
    search_fields = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ класс для управления ингредиентами."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class TagsInline(admin.TabularInline):
    """Инлайн класс тэгов для отображения в рецепте."""

    model = Recipe.tags.through
    extra = 0
    verbose_name = Tag._meta.verbose_name
    verbose_name_plural = Tag._meta.verbose_name_plural


class IngredientInline(admin.TabularInline):
    """Инлайн класс ингредиентов для отображения в рецепте."""

    model = Recipe.ingredients.through
    extra = 0
    verbose_name = Ingredient._meta.verbose_name
    verbose_name_plural = Ingredient._meta.verbose_name_plural


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ класс для управления рецептами."""

    list_display = ('id', 'name', 'author', 'favorites_amount')
    list_select_related = ('author',)
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags__name',)
    inlines = (TagsInline, IngredientInline)
    readonly_fields = ('favorites_amount', )

    # fieldsets = (
    #     (None, {'fields': ('name', 'author',)}),
    #     ('Количество добавлений в избранное', {
    #         'fields': ('favorites_amount',)
    #     }),
    # )

    def get_fieldsets(self, request, obj=None):
        """Метод подготовки полей админки рецепта."""
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets

    @admin.display(description='Количество добавлений в избранное',)
    def favorites_amount(self, recipe):
        """Метод для подсчета количества подписок на рецепт."""
        return recipe.favorites.count()


class FavoriteShoppingCartBaseAdmin(admin.ModelAdmin):
    """Базовый класс для избранного и корзины покупок."""

    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_select_related = ('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(FavoriteShoppingCartBaseAdmin):
    """Админ класс для управления списком избранных рецептов."""


@admin.register(ShoppingCart)
class ShoppingCartAdmin(FavoriteShoppingCartBaseAdmin):
    """Админ класс для управления корзиной покупок."""


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ класс для управления подписками на авторов."""

    list_display = ('user', 'author',)
    search_fields = ('user__username', 'user__email', 'author__username')
    list_select_related = ('user', 'author')
