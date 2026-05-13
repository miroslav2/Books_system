-- ============================================================
--  Миграция: система выдачи книг
--  Выполнить один раз в базе данных books_data
-- ============================================================

-- 1. Добавить статус выдачи в таблицу books
ALTER TABLE books
    ADD COLUMN IF NOT EXISTS is_loaned BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Таблица истории выдач
CREATE TABLE IF NOT EXISTS loans (
    id            SERIAL PRIMARY KEY,
    book_id       INT          NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    borrower_name VARCHAR(200) NOT NULL,
    loaned_at     DATE         NOT NULL DEFAULT CURRENT_DATE,
    due_date      DATE,
    returned_at   DATE,                        -- NULL = ещё не возвращена
    note          VARCHAR(500)
);

-- Индекс для быстрого поиска активных выдач по книге
CREATE INDEX IF NOT EXISTS idx_loans_book_active
    ON loans(book_id)
    WHERE returned_at IS NULL;
