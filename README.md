# 📚 Books System

Десктопное приложение для управления домашней библиотекой. Позволяет хранить информацию о книгах с привязкой к физическому местоположению: квартира → шкаф → полка, отслеживать выданные книги и анализировать коллекцию через графики.

Написано на **Python** с использованием **PyQt6** и **PostgreSQL**.

---

## Возможности

- Подключение к PostgreSQL с сохранением настроек подключения
- Полный CRUD для книг: добавление, редактирование, удаление
- Управление хранилищем: квартиры, шкафы, полки (с переносом между уровнями иерархии)
- Поиск по любому полю таблицы с выбором критерия из выпадающего списка
- Система выдачи книг: отметить книгу как выданную (кому, когда, до какого числа), зафиксировать возврат, просматривать историю выдач
- Фильтр «Выданные» для быстрого просмотра книг, которые сейчас на руках
- Статистика коллекции: графики по авторам, языкам, годам, издательствам, жанрам, а также круговая диаграмма жанров среди выданных книг
- Тёмная тема оформления в стиле Ubuntu
- Сборка в автономный `.exe` через PyInstaller

---

## Структура проекта

```
Books_system/
├── assets/
│   └── icon.ico              # Иконка приложения
├── database/
│   └── data_system.py        # Класс работы с БД (psycopg2)
├── ui/
│   ├── main_window.py        # Окно подключения к БД
│   ├── books_tab.py          # Главное окно: таблица книг, выдача, хранилище
│   └── statistic_tab.py      # Панель статистики (matplotlib)
├── main.py                   # Точка входа
├── main.spec                 # Конфигурация сборки PyInstaller
├── style.qss                 # Стили (Ubuntu Dark Theme)
├── migration_loans.sql       # SQL-миграция для системы выдачи книг
├── .env.example              # Пример файла переменных окружения
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
                                isbn, language, shelf_level_id,
                                is_loaned)
                            └── loans (id, book_id, borrower_name,
                                       loaned_at, due_date,
                                       returned_at, note)
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
    shelf_level_id   INT REFERENCES shelf_levels(id),
    is_loaned        BOOLEAN NOT NULL DEFAULT FALSE
);
```

**6. Применить миграцию системы выдачи**

Если база данных уже существует и таблица `books` создана без колонки `is_loaned`, выполнить `migration_loans.sql` в pgAdmin или psql:

```bash
psql -U postgres -d books_data -f migration_loans.sql
```

Если база создаётся с нуля — таблицы из пункта 5 уже включают `is_loaned`, а таблицу `loans` всё равно нужно создать из миграции:

```sql
CREATE TABLE IF NOT EXISTS loans (
    id            SERIAL PRIMARY KEY,
    book_id       INT          NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    borrower_name VARCHAR(200) NOT NULL,
    loaned_at     DATE         NOT NULL DEFAULT CURRENT_DATE,
    due_date      DATE,
    returned_at   DATE,
    note          VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_loans_book_active
    ON loans(book_id)
    WHERE returned_at IS NULL;
```

**7. Запустить приложение**

```bash
python main.py
```

---

## Зависимости

| Пакет | Назначение |
|---|---|
| PyQt6 | GUI |
| psycopg2 | Подключение к PostgreSQL |
| pandas | Работа с табличными данными |
| matplotlib | Графики статистики |
| python-dotenv | Загрузка переменных окружения |
| pillow | Конвертация изображений (для иконки при сборке) |
| pyinstaller | Сборка в автономный .exe |

---

## Использование

После запуска откроется окно подключения. Введите параметры БД (или они подгрузятся автоматически, если включено «Запомнить настройки»).

В главном окне доступны:

**Таблица книг** — поиск с выбором критерия (название, автор, год, издательство, город, стиль, язык, шкаф, квартира, выданные), сортировка по столбцам, добавление, редактирование, удаление. Выданные книги подсвечиваются красным.

**📖 Выдать / ↩ Вернуть** — кнопка в тулбаре меняет подпись в зависимости от статуса выбранной книги. При выдаче указывается получатель, дата выдачи и планируемая дата возврата. При возврате фиксируется дата. Через кнопку «История выдач» в диалоге можно посмотреть все прошлые операции по книге.

**🏠 Хранилище** — управление квартирами, шкафами и полками. Поддерживает перенос шкафа в другую квартиру и полки в другой шкаф.

**📊 Статистика** — панель с графиками, открывается рядом с таблицей. Доступные графики: по авторам, языкам, годам, издательствам, городам, жанрам (количество и %), а также круговая диаграмма жанров среди книг, которые сейчас на руках.

---

## Сборка в .exe

Проект поддерживает сборку в автономный исполняемый файл через PyInstaller.

**Сборка:**

```bash
pyinstaller main.spec
```

Готовый `.exe` появится в папке `dist/`.

**Что включено в сборку (`main.spec`):**

```python
datas=[
    ('style.qss', '.'),          # файл стилей
    ('assets\\icon.ico', 'assets'),  # иконка приложения
],
```

---

## Лицензия

[MIT](LICENSE) — используй свободно, ссылка на автора приветствуется.

---

*Автор: Dobry_Slav*

