from datetime import date

from babel.dates import format_date

SHOPPING_CART_TITLE = (
    f'Список покупок от {format_date(date.today(), "dd MMMM yyyy", locale="ru")}.'
)
SHOPPING_CART_RECIPES = '   \u2022 {} (Автор - {})'
SHOPPING_CART_PRODUCTS = '  {}. {} - {} ({})'


def get_shopping_cart_text(ingredients, recipes, domain):
    """Метод для формирования текса скачиваемой корзины покупок."""
    return '\n'.join([
        SHOPPING_CART_TITLE,
        '-' * len(SHOPPING_CART_TITLE),
        '',
        'Для приготовления рецептов:',
        '',
        *{SHOPPING_CART_RECIPES.format(
            recipe['recipe__name'],
            recipe['recipe__author__username'],
        ) for recipe in recipes},
        '',
        'Понадобятся следующие продукты:'
        '',
        '',
        *[SHOPPING_CART_PRODUCTS.format(
            count,
            ingredient['ingredient__name'].capitalize(),
            ingredient['sum'],
            ingredient['ingredient__measurement_unit']
        ) for count, ingredient in enumerate(ingredients, 1)],
        '',
        '',
        f'Загружено с сайта: {domain}'
    ])
