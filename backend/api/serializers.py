from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer
)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.admin import User
from recipes.models import (
    MAX_COOKING_TIME, MAX_INGREDIENT_AMOUNT, MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT, Ingredient, Recipe, RecipeIngredient, Tag
)

REQUIRED_FIELD = 'Обязательное поле.'
NOT_EMPTY_FIELD = 'Поле не должно быть пустым!'
ITEMS_NOT_REPEAT_ERROR = 'Значения не должны повторяться: {}'


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(BaseUserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        fields = (*BaseUserSerializer.Meta.fields, 'is_subscribed', 'avatar',)
        read_only_fields = fields

    def get_is_subscribed(self, author):
        """Метод получения значения подписки на конкретного автора."""
        return (
            (user := self.context['request'].user)
            and user.is_authenticated
            and user.user_subscriptions.filter(author=author).exists()
        )


class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class AuthorSerializer(UserSerializer):
    """Сериализатор для показа информации об авторах рецетов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count',)
        read_only_fields = fields

    def get_recipes(self, user):
        """Метод получения рецептов с возможностью ограничить по количеству."""
        return RecipeShortSerializer(
            user.recipes.all()[:int(
                self.context['request'].GET.get('recipes_limit', 10**10)
            )],
            many=True
        ).data


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор чтения продуктов рецепта."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = ('amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор чтения рецепта."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'name', 'text',
            'cooking_time',
            'author',
            'tags',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = fields

    def get_user_related_fields(self, recipe, related_name):
        """Метод для проверки существования связанной записи."""
        return (
            (user := self.context['request'].user)
            and user.is_authenticated
            and getattr(user, related_name).filter(recipe=recipe).exists()
        )

    def get_is_favorited(self, recipe):
        """Метод для определения в избранном ли рецепт."""
        return self.get_user_related_fields(recipe, 'favorites')

    def get_is_in_shopping_cart(self, recipe):
        """Метод для определения в корзине покупок ли рецепт."""
        return self.get_user_related_fields(recipe, 'shoppingcarts')


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания продуктов рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT
    )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецепта."""

    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'image',
        )

    def validate(self, data):
        """Общая валидация."""
        for field in ['ingredients', 'tags']:
            if not data.get(field):
                raise serializers.ValidationError({field: REQUIRED_FIELD})
        return data

    def unique_validate(self, items):
        """Метод проверки уникальности передаваемых значений."""
        if repeats := [item.name for item in items if items.count(item) > 1]:
            raise serializers.ValidationError(
                ITEMS_NOT_REPEAT_ERROR.format(', '.join(set(repeats)))
            )

    def validate_ingredients(self, recipe_ingredient_data):
        """Валидация продуктов."""
        self.unique_validate([
            ingredient_data['ingredient'] for ingredient_data
            in recipe_ingredient_data
        ])
        return recipe_ingredient_data

    def validate_tags(self, tags):
        """Валидация тэгов."""
        self.unique_validate(tags)
        return tags

    @transaction.atomic
    def create_tags_ingredients(
        self, recipe, ingredients, tags
    ):
        """Создание тэгов и продуктов рецепта."""
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ) for ingredient in ingredients)
        return recipe

    def create(self, recipe_data):
        ingredients = recipe_data.pop('ingredients')
        tags = recipe_data.pop('tags')
        return self.create_tags_ingredients(
            recipe=super().create(recipe_data),
            ingredients=ingredients,
            tags=tags
        )

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        self.create_tags_ingredients(
            recipe=instance,
            ingredients=ingredients,
            tags=tags,
        )
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        """Метод для выдачи сериализатора рецепта для чтения."""
        return RecipeReadSerializer(recipe, context=self.context).data
