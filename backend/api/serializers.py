import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.admin import User
from recipes.models import (
    Ingredient, Favorite, Recipe, RecipeIngredient, ShoppingCart, Subscription,
    Tag
)

REQUIRED_FIELD = 'Обязательное поле.'
NOT_EMPTY_FIELD = 'Поле не должно быть пустым!'
ITEMS_NOT_REPEAT_ERROR = 'Значения не должны повторяться: {}'
ITEMS_NOT_FOUND_ERROR = 'В списке доступных нет значения: {}!'
INGREDIENTS_MIN_VALUE = 1
COOKING_TIME_MIN_VALUE = 1


class Base64ImageField(serializers.ImageField):
    """Класс для преобразования переданной картинки."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            img_format, img_str = data.split(';base64,')
            ext = img_format.split('/')[-1]
            data = ContentFile(base64.b64decode(img_str), name='image.' + ext)
        return super().to_internal_value(data)


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

    def get_is_subscribed(self, obj):
        """Метод получения значения подписки на конкретного автора."""
        return (
            (user := self.context['request'].user)
            and user.is_authenticated
            and user.subscribers.filter(author=obj).exists()
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
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class SubscriptionsSerializer(UserSerializer):
    """Сериализатор для показа подписок пользователя."""

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
        request = user.recipes.all()
        if recipes_limit := self.context['request'].GET.get('recipes_limit'):
            request = request[:int(recipes_limit)]
        return RecipeShortSerializer(request, many=True).data


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    class Meta():
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Подписка на этого автора оформлена ранее!'
            )
        ]

    def validate_author(self, author):
        """Метод валидации подписки самого на себя."""
        if author == self.context['request'].user:
            raise ValidationError('Подписка на самого себя запрещена!')
        return author


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор чтения ингредиентов рецепта."""

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

    def get_is_favorited(self, recipe):
        """Метод для определения в избранном ли рецепт."""
        return (
            (user := self.context['request'].user)
            and user.is_authenticated
            and user.favorites.filter(recipe_id=recipe.id).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        """Метод для определения в корзине покупок ли рецепт."""
        return (
            (user := self.context['request'].user)
            and user.is_authenticated
            and user.shoppingcarts.filter(recipe_id=recipe.id).exists()
        )


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания ингредиентов рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField(min_value=INGREDIENTS_MIN_VALUE)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=COOKING_TIME_MIN_VALUE)

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
        if repeats := [item for item in items if items.count(item) > 1]:
            raise serializers.ValidationError(
                ITEMS_NOT_REPEAT_ERROR.format(repeats)
            )

    def validate_ingredients(self, recipe_ingredient_data):
        """Валидация ингредиентов."""
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
        """Создание тэгов и ингредиентов рецепта."""
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


class FavoriteSerializer(serializers.ModelSerializer):
    """Работа с избранными рецептами."""

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe',)

        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное.'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Работа со списком покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe',)

        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок.'
            )
        ]
