# Foodgram — продуктовый помощник

## Описание проекта

Онлайн-сервис для публикации рецептов и управления покупками. Основные возможности проекта включают создание и редактирование своих рецептов. Управление распределено на роли обычного неавторизованного пользователя, автора и администратора. Помимо работы с рецептами, зарегистрированные пользователи могут подписываться на других авторов, добавлять в избранное понравившиеся рецепты, также скачивать список ингредиентов любимых рецептов для упрощения покупок. В проекте реализована возможность формировать короткую ссылку на рецепт.

### Текущий статус workflow
[![Main Foodgram workflow](https://github.com/shibaevvv/foodgram/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/shibaevvv/foodgram/actions/workflows/main.yml)

## Технологический стек

  - Python
  - Django
  - Django Rest Framework
  - React
  - Docker
  - PostgreSQL
  - Nginx
  - Gunicorn
  - GitHub actions


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

Для наполнения тестовыми данными (теги, ингредиенты) выполните загрузку:
```bash
docker compose exec backend python manage.py load_data ingredients.json
docker compose exec backend python manage.py load_data tags.json
```
Файлы для ingredients.csv и tags.csv должны лежать в каталоге /backend/data

#### Основные страницы
- По адресу [http://localhost](http://localhost) изучите фронтенд веб-приложения

- По адресу [http://localhost/api/docs/](http://localhost/api/docs/)— спецификацию API

- Админка доступна тут [http://localhost/admin/](http://localhost/admin/)

Для создания суперпользователя выполните:
```bash
docker compose exec backend python manage.py createsuperuser
```

## Локальный запуск бэкенд части проекта

Чтобы не разворачивать базу данных POSTGRES, выполните смену типа на SQLITE в
файле .env (см.раздел "Описание .env").

```bash
echo 'SQLITE=True' >> .env
```
Для запуска необходим установленный Python (рабочая версия 3.12.7)

После клонирования перейдите в каталог backend.
Создайте и активируйте виртуальное окружение.
Обновите pip и установити зависимости:
```bash
cd foodgram/backend
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Выполните миграции, загрузку данных тестовых (если необходимо) и запуск сервера:
```bash
python manage.py migrate
python manage.py load_data ingredients.json
python manage.py load_data tags.json
python manage.py runserver
```
#### Основные страницы при локальном запуске только бэкенд части

- По адресу [127.0.0.1:8000](http://127.0.0.1:8000) изучите веб-приложения

- Админка доступна тут [127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)


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
echo 'CSRF_TRUSTED_ORIGINS=https://mydomain.net' >> .env
```

## Автор

- [Владимир Шибаев](https://github.com/shibaevvv)
[![Email Badge](https://img.shields.io/badge/-Email-D14836?style=flat&logo=Gmail&logoColor=white)](mailto:shibaev.vladimir@gmail.com) [![Telegram Badge](https://img.shields.io/badge/-Telegram-blue?style=flat&logo=Telegram&logoColor=white)](https://t.me/markvaaa)