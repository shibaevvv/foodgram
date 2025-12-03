from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.db import models

EMAIL_MAX_LENGTH = 254
USERNAME_MAX_LENGTH = 150
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGHT = 150
TAG_MAX_MAX_LENGHT = 25
RECIPE_NAME_MAX_LENGTH = 256
COOKING_MIN_TIME = 1


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
        'Фото профиля',
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
        related_name='subscribers',
    )
    author = models.ForeignKey(
        User,
        verbose_name='на кого подписан',
        on_delete=models.CASCADE,
        related_name='subscriptions',
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
        'Имя тэга',
        max_length=TAG_MAX_MAX_LENGHT,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=TAG_MAX_MAX_LENGHT,
        unique=True,
    )

    class Meta:
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField('Название')
    measurement_unit = models.CharField('Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        # ordering = ('name',)
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
        verbose_name='Список ингредиентов',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список id тегов',
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes',
        blank=True,
    )
    name = models.CharField(
        'Название рецепта',
        blank=False,
        max_length=RECIPE_NAME_MAX_LENGTH,
    )
    text = models.TextField(
        'Текст рецепта',
        blank=False,
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        blank=False,
        validators=[
            MinValueValidator(COOKING_MIN_TIME)
        ],
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-id',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта с ингредиентами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField('Количество',)

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        default_related_name = 'recipe_ingredients'
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
        verbose_name = 'списки покупок'
        verbose_name_plural = 'Список покупок'
