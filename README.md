# Foodgram — продуктовый помощник

## Описание проекта

Онлайн-сервис для публикации рецептов и управления покупками. Основные возможности проекта включают создание и редактирование своих рецептов. Управление распределено на роли обычного неавторизованного пользователя, автора и администратора. Помимо работы с рецептами, зарегистрированные пользователи могут подписываться на других авторов, добавлять в избранное понравившиеся рецепты, также скачивать список ингредиентов любимых рецептов для упрощения покупок. В проекте реализована возможность формировать короткую ссылку на рецепт.

### Текущий статус workflow
[![Main Kittygram workflow](https://github.com/shibaevvv/foodgram/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/shibaevvv/foodgram/actions/workflows/main.yml)

## Технологический стек

<ul>
  <li>Python</li>
  <li>Django</li>
  <li>Django Rest Framework</li>
  <li>React</li>
  <li>Docker</li>
  <li>PostgreSQL</li>
  <li>Nginx</li>
  <li>Gunicorn</li>
  <li>GitHub actions</li>
</ul>

## Локальное развертывание и запуск проекта

На вашем компьютере должен быть установлен Docker.

Клонировать репозиторий и перейти в него в командной строке:
```python
git clone https://github.com/shibaevvv/foodgram.git
cd foodgram
```
Создать файл .env и заполнить его по образцу .env.template. (см.раздел "Описание .env")

Запустить контейнеры используя конфигурацию 
```bash
docker compose up
```

Выполнить сбор статических файлов, их перенос в общий volumes и миграции БД.
```bash
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py migrate
```

Для наполнения тестовыми данными (теги, ингердиенты) выполните загрузку:
```bash
docker compose exec backend python manage.py load_data --wipe
```
Ключ --wipe очищает базу перед добавлением.
Файлы для ingredients.csv и tags.csv должны лежать в каталоге /backend/data

#### Основные страницы
По адресу http://localhost изучите фронтенд веб-приложения
по адресу http://localhost/api/docs/ — спецификацию API
Админка доступна тут http://localhost/admin/

Для создания суперпользователя выполните:
```bash
docker compose exec backend python manage.py createsuperuser
```

## Описание .env
#### Пример заполнения файла .env смотрите в .env.example

```bash
echo 'SQLITE=False' >> .env
echo 'POSTGRES_DB=foodgram' >> .env
echo 'POSTGRES_USER=foodgram_user' >> .env
echo 'POSTGRES_PASSWORD=foodgram_password' >> .env
echo 'DB_HOST=db' >> .env
echo 'DB_PORT=5432' >> .env
echo 'SECRET_KEY=secret_key' >> .env
echo 'DEBUG=False' >> .env
echo 'ALLOWED_HOSTS=127.0.0.1,localhost' >> .env
```

## Автор

- [Владимир Шибаев](https://github.com/shibaevvv)
