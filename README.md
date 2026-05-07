# 📚 Books System

Десктопное приложение для управления домашней библиотекой. Позволяет хранить информацию о книгах с привязкой к физическому местоположению: квартира → шкаф → полка.

Написано на **Python** с использованием **PyQt6** и **PostgreSQL**.

---

## Возможности

- Подключение к PostgreSQL с сохранением настроек
- Полный CRUD для книг: добавление, редактирование, удаление
- Управление хранилищем: квартиры, шкафы, полки (с переносом между уровнями)
- Поиск по любому полю таблицы с выбором критерия
- Статистика коллекции: графики по авторам, языкам, годам, издательствам, жанрам
- Тёмная тема оформления в стиле Ubuntu

---

## Структура проекта

```
Books_system/
├── database/
│   └── data_system.py      # Класс работы с БД (psycopg2)
├── ui/
│   ├── main_window.py      # Окно подключения к БД
│   ├── books_tab.py        # Главное окно: таблица книг + управление хранилищем
│   └── statistic_tab.py    # Панель статистики (matplotlib)
├── main.py                 # Точка входа
├── style.qss               # Стили (Ubuntu Dark Theme)
├── .env.example            # Пример файла переменных окружения
└── .gitignore
```

---

## Схема базы данных

```
apartments (id, name)
    └── shelves (id, name, apartment_id)
            └── shelf_levels (id, name, shelf_id)
                    └── books (id, title, author, publication_year,
                                publisher, city, stile, pages,
                                isbn, language, shelf_level_id)
```

---

## Установка

**1. Клонировать репозиторий**

```bash
git clone https://github.com/miroslav2/Books_system.git
cd Books_system
```

**2. Создать и активировать виртуальное окружение**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

**3. Установить зависимости**

```bash
pip install -r requirements.txt
```

**4. Настроить подключение к БД**

Скопировать `.env.example` в `.env` и заполнить:

```bash
cp .env.example .env
```

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=books_data
DB_USER=postgres
DB_PASSWORD=your_password
```

**5. Создать таблицы в PostgreSQL**

```sql
CREATE TABLE apartments (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE shelves (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    apartment_id INT REFERENCES apartments(id) ON DELETE CASCADE
);

CREATE TABLE shelf_levels (
    id       SERIAL PRIMARY KEY,
    name     INT NOT NULL,
    shelf_id INT REFERENCES shelves(id) ON DELETE CASCADE
);

CREATE TABLE books (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(300) NOT NULL,
    author           VARCHAR(300) NOT NULL,
    publication_year INT,
    publisher        VARCHAR(300),
    city             VARCHAR(200),
    stile            VARCHAR(300),
    pages            INT,
    isbn             VARCHAR(50),
    language         VARCHAR(100),
    shelf_level_id   INT REFERENCES shelf_levels(id)
);
```

**6. Запустить приложение**

```bash
python main.py
```

---

## Зависимости

| Пакет | Назначение |
|---|---|
| PyQt6 | GUI |
| psycopg2-binary | Подключение к PostgreSQL |
| pandas | Работа с табличными данными |
| matplotlib | Графики статистики |
| python-dotenv | Загрузка переменных окружения |

---

## Использование

После запуска откроется окно подключения. Введите параметры БД (или они подгрузятся автоматически, если включено «Запомнить настройки»).

В главном окне доступны:

- **Таблица книг** — поиск, сортировка, добавление, редактирование, удаление
- **🏠 Хранилище** — управление квартирами, шкафами и полками
- **📊 Статистика** — панель с графиками, открывается рядом с таблицей

---

## Лицензия

MIT
