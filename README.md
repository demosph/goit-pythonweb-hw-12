# Тема 10. Домашня робота

### Технічний опис завдання

- Реалізуйте механізм аутентифікації в застосунку.
- Реалізуйте механізм авторизації за допомогою JWT-токенів, щоб усі операції з контактами проводились лише зареєстрованими користувачами.
- Користувач повинен мати доступ лише до своїх операцій з контактами.
- Реалізуйте механізм верифікації електронної пошти зареєстрованого користувача.
- Обмежте кількість запитів до маршруту користувача /me.
- Увімкніть CORS для свого REST API.
- Реалізуйте можливість оновлення аватара користувача (використовуйте сервіс Cloudinary).

### Налаштування середовища і запуск програми

1. Перейдіть в діректорію проекта:

`cd goit-pythonweb-hw-10`

2. Створіть та налаштуйте .env файл у корені проєкту за прикладом:

```
JWT_SECRET=<your jwt secret>

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=<your db password>
DB_PORT=5432
DB_HOST=db
DB_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

MAIL_USERNAME=<your email address>
MAIL_PASSWORD=<your email password>
MAIL_FROM=<your email address>

CLD_NAME=<your cloudinary name>
CLD_API_KEY=<your cloudinary API key>
CLD_API_SECRET=<your cloudinary API secret>
```

3. Використайте Docker Compose для побудови і запуску середовища:

`docker-compose up --build`

4. Для взаємодії з сервером ми можемо надсилати запити за допомогою Swagger за адресою http://127.0.0.1:8000/docs#/.