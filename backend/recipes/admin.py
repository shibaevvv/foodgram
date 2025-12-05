from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from recipes.models import (
    Ingredient, Favorite, Recipe, ShoppingCart, Subscription, Tag
)

User = get_user_model()

admin.site.empty_value_display = 'Не задано'


class RecipesCountMixin:
    """Миксин для определения количества рецептов объекта."""

    @admin.display(description='Рецептов')
    def recipes_count(self, model):
        return model.recipes.count()
    

class BaseListFilter(admin.SimpleListFilter):
    """Базовый класс для фильтров."""

    def lookups(self, request, model_admin):
        return [(1, 'Да'), (0, 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(
                **{f'{self.parameter_name}__isnull': False}).distinct()
        elif self.value() == '0':
            return queryset.filter(**{f'{self.parameter_name}__isnull': True})


class HasRecipesFilter(BaseListFilter):
    """Фильтр наличия рецептов."""

    title = 'Имеет рецепты'
    parameter_name = 'recipes'


class HasUserSubscriptionsFilter(BaseListFilter):
    """Фильтр наличия подписок."""

    title = 'Имеет подписки'
    parameter_name = 'user_subscriptions'


class HasAuthorSubscriptionsFilter(BaseListFilter):
    """Фильтр наличия подписчиков."""

    title = title = 'Имеет подписчиков'
    parameter_name = 'author_subscriptions'


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр по времени готовки рецепта."""

    title = 'Время (мин)'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        cooking_times = sorted(
            set(
                model_admin.model.objects.all().values_list(
                    'cooking_time',
                    flat=True
                )
            )
        )
        if (count := len(cooking_times)) < 3:
            return []
        self.max_fast_limit = cooking_times[count // 3]
        self.min_slow_limit = cooking_times[count // 3 * 2]
        return [
            ('fast', f'< {self.max_fast_limit} мин.'),
            ('middle', f'{self.max_fast_limit} - {self.min_slow_limit} мин.'),
            ('long', f'> {self.min_slow_limit} мин.'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(
                **{f'{self.parameter_name}__lt': self.max_fast_limit}
            )
        elif self.value() == 'middle':
            return queryset.filter(
                **{f'{self.parameter_name}__range': (
                    self.max_fast_limit, self.min_slow_limit
                )}
            )
        elif self.value() == 'long':
            return queryset.filter(
                **{f'{self.parameter_name}__gt': self.min_slow_limit}
            )


@admin.register(User)
class UserAdmin(BaseUserAdmin, RecipesCountMixin):
    """Админ класс для управления пользователями."""

    fieldsets = BaseUserAdmin.fieldsets + ((None, {'fields': ('avatar',)}),)
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_thumbnail',
        'is_staff',
        'recipes_count',
        'user_subscriptions_count',
        'author_subscriptions_count'
    )
    list_display_links = ('username',)
    list_filter = (
        HasRecipesFilter,
        HasUserSubscriptionsFilter,
        HasAuthorSubscriptionsFilter,
    )
    search_fields = ('username', 'email',)
    ordering = ('username',)

    @admin.display(description='ФИО')
    def full_name(self, user):
        """Метод для вычисления ФИО."""
        return f'{user.first_name} {user.last_name}'
    
    @admin.display(description='Аватар')
    @mark_safe
    def avatar_thumbnail(self, user):
        """Метод для вычисления кода аватара."""
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="35" height="35" />'
    
    @admin.display(description='Подписок')
    def user_subscriptions_count(self, user):
        """Метод для вычисления подписок."""
        return user.user_subscriptions.count()
    
    @admin.display(description='Подписчиков')
    def author_subscriptions_count(self, user):
        """Метод для вычисления подписчиков."""
        return user.author_subscriptions.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin, RecipesCountMixin):
    """Админ класс для управления тегами."""

    list_display = ('id', 'name', 'slug', 'recipes_count',)
    search_fields = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin, RecipesCountMixin):
    """Админ класс для управления продуктами."""

    list_display = ('id', 'name', 'measurement_unit', 'recipes_count',)
    search_fields = ('name', 'measurement_unit', )
    list_filter = (HasRecipesFilter, )


class TagsInline(admin.TabularInline):
    """Инлайн класс тэгов для отображения в рецепте."""

    model = Recipe.tags.through
    extra = 0
    verbose_name = Tag._meta.verbose_name
    verbose_name_plural = Tag._meta.verbose_name_plural


class IngredientInline(admin.TabularInline):
    """Инлайн класс продуктов для отображения в рецепте."""

    model = Recipe.ingredients.through
    extra = 0
    verbose_name = Ingredient._meta.verbose_name
    verbose_name_plural = Ingredient._meta.verbose_name_plural


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ класс для управления рецептами."""

    list_display = ('id', 'name', 'cooking_time', 'author',
        'favorites_amount', 'ingredients_list', 'tags_list', 'image_thumbnail')
    list_select_related = ('author',)
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'tags__name',
        'ingredients__name',
    )
    list_filter = ('tags__name', 'author__username', CookingTimeFilter,)
    inlines = (TagsInline, IngredientInline)
    readonly_fields = ('favorites_amount', )

    @admin.display(description='В избранном',)
    def favorites_amount(self, recipe):
        """Метод для подсчета количества подписок на рецепт."""
        return recipe.favorites.count()
    
    @admin.display(description='Картинка')
    @mark_safe
    def image_thumbnail(self, recipe):
        return f'<img src="{recipe.image.url}" width="35" height="35" />'

    @admin.display(description='Тэги')
    @mark_safe
    def tags_list(self, recipe):
        return ', '.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_list(self, recipe):
        return ', '.join(
            f'{ingredient.ingredient.name} - {ingredient.amount}'
            f' {ingredient.ingredient.measurement_unit}'
            for ingredient in recipe.recipe_ingredients.all()
        )


@admin.register(Favorite, ShoppingCart)
class FavoriteShoppingCartBaseAdmin(admin.ModelAdmin):
    """Админ класс для управления избранным и корзиной покупок."""

    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_select_related = ('user', 'recipe')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ класс для управления подписками на авторов."""

    list_display = ('user', 'author',)
    search_fields = ('user__username', 'user__email', 'author__username')
    list_select_related = ('user', 'author')
