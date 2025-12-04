from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

EMAIL_MAX_LENGTH = 254
USERNAME_MAX_LENGTH = 150
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGHT = 150
TAG_MAX_LENGHT = 32
RECIPE_NAME_MAX_LENGTH = 256
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 2147483647
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 2147483647
INGREDIENT_NAME_MAX_LENGHT = 128
MEASUREMENT_UNIT_MAX_LENGHT = 64


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Логин',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),),
    )
    first_name = models.CharField(
        'Имя',
        max_length=FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LAST_NAME_MAX_LENGHT,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatar',
        blank=True,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки на автора."""

    user = models.ForeignKey(
        User,
        verbose_name='кто подписан',
        on_delete=models.CASCADE,
        related_name='user_subscriptions',
    )
    author = models.ForeignKey(
        User,
        verbose_name='на кого подписан',
        on_delete=models.CASCADE,
        related_name='author_subscriptions',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'


class Tag(models.Model):
    """Модель тэга."""

    name = models.CharField(
        'Имя',
        max_length=TAG_MAX_LENGHT,
        unique=True,
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=TAG_MAX_LENGHT,
        unique=True,
    )

    class Meta:
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель продукта."""

    name = models.CharField(
        'Название',
        max_length=INGREDIENT_NAME_MAX_LENGHT,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGHT,
    )

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} / {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Продукты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes',
        blank=True,
    )
    name = models.CharField(
        'Название',
        blank=False,
        max_length=RECIPE_NAME_MAX_LENGTH,
    )
    text = models.TextField(
        'Описание',
        blank=False,
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        blank=False,
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ]
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта с продуктами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
        related_name='ingredient_in_recipes',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
        ]
    )

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')

    class Meta:
        verbose_name = 'продукт рецепта'
        verbose_name_plural = 'Продукты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipe_ingredient',
            ),
        ]


class UserRecipeBaseModel(models.Model):
    """Базовая модель связи рецепта с пользователем."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]
        abstract = True
        default_related_name = '%(class)ss'

    def __str__(self):
        return f'У {self.user.username} в списке {self.recipe}'


class Favorite(UserRecipeBaseModel):
    """Модель связи рецепта с пользователем (избранное)."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeBaseModel):
    """Модель связи рецепта с пользователем (корзина покупок)."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списоки покупок'
