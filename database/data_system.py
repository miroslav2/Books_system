import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

class Data_system:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )

            self.cursor = self.conn.cursor()

            print('SQL connected')
        except psycopg2.Error as e:
            print(f'SQL error: {e}')

    def disconnect(self):
        self.cursor.close()
        self.conn.close()
        print('SQL disconnected')

    def _execute(self, query, params=None, fetch=False):
        try:
            self.cursor.execute(query, params)
            if fetch:
                return self.cursor.fetchall()
            else:
                self.conn.commit()
                return None
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"SQL error: {e}")
            raise

# ---------------apartments---------------

    def get_apartments(self) -> pd.DataFrame:
        rows = self._execute("SELECT * FROM apartments ORDER BY id", fetch=True)
        return pd.DataFrame(rows, columns=["id", "name"])
    
    def insert_apartments(self, name: str):
        self._execute("INSERT INTO apartments (name) VALUES (%s)", (name,))
    
    def update_apartments(self, apartment_id: int, name: str):
        self._execute("UPDATE apartments SET name=%s WHERE id=%s", (name, apartment_id))
    
    def delete_apartments(self, apartment_id: int):
        self._execute("DELETE FROM apartments WHERE id=%s", (apartment_id,))

# ---------------shelves---------------

    def get_shelves(self) -> pd.DataFrame:
        rows = self._execute("SELECT * FROM shelves ORDER BY id", fetch=True)
        return pd.DataFrame(rows, columns=["id", "name"])
    
    def insert_shelves(self, name: str, apartment_id: int):
        self._execute("INSERT INTO shelves (name, apartment_id) VALUES (%s, %s)", (name, apartment_id))
    
    def update_shelves(self, shelves_id: int, name: str):
        self._execute("UPDATE shelves SET name=%s WHERE id=%s", (name, shelves_id))
    
    def delete_shelves(self, shelves_id: int):
        self._execute("DELETE FROM shelves WHERE id=%s", (shelves_id,))

# ---------------shelf levels---------------

    def get_shelf_levels(self) -> pd.DataFrame:
        rows = self._execute("SELECT * FROM shelf_levels ORDER BY id", fetch=True)
        return pd.DataFrame(rows, columns=["id", "name"])
    
    def insert_shelf_levels(self, name: str, shelf_id: int):
        self._execute("INSERT INTO shelf_levels (name, shelf_id) VALUES (%s, %s)", (name, shelf_id))
    
    def update_shelf_levels(self, shelf_levels_id: int, name: str):
        self._execute("UPDATE shelf_levels SET name=%s WHERE id=%s", (name, shelf_levels_id))
    
    def delete_shelf_levels(self, shelf_levels_id: int):
        self._execute("DELETE FROM shelf_levels WHERE id=%s", (shelf_levels_id,))

# ---------------books---------------

    def get_books(self, search: str = None) -> pd.DataFrame:
        base_query = """
            SELECT b.id, b.title, b.author, b.publication_year,
                   b.publisher, b.city, b.stile, b.pages,
                   b.isbn, b.language,
                   sl.name as shelf_level, s.name as shelf, a.name as apartment
            FROM books b
            JOIN shelf_levels sl ON b.shelf_level_id = sl.id
            JOIN shelves s       ON sl.shelf_id = s.id
            JOIN apartments a    ON s.apartment_id = a.id
        """
        if search:
            base_query += " WHERE b.title ILIKE %s OR b.author ILIKE %s"
            rows = self._execute(base_query + " ORDER BY b.title",
                                 (f"%{search}%", f"%{search}%"), fetch=True)
        else:
            rows = self._execute(base_query + " ORDER BY b.title", fetch=True)

        columns = ["id", "title", "author", "year", "publisher",
                   "city", "style", "pages", "isbn", "language",
                   "shelf_level", "shelf", "apartment"]
        return pd.DataFrame(rows, columns=columns)

    def insert_book(self, title, author, year, publisher, city,
                    style, pages, isbn, language, shelf_level_id):
        self._execute("""
            INSERT INTO books (title, author, publication_year, publisher,
                               city, stile, pages, isbn, language, shelf_level_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (title, author, year, publisher, city, style, pages, isbn, language, shelf_level_id))

    def update_book(self, book_id, title, author, year, publisher, city,
                    style, pages, isbn, language, shelf_level_id):
        self._execute("""
            UPDATE books SET title=%s, author=%s, publication_year=%s,
                publisher=%s, city=%s, stile=%s, pages=%s,
                isbn=%s, language=%s, shelf_level_id=%s
            WHERE id=%s
        """, (title, author, year, publisher, city, style, pages, isbn, language, shelf_level_id, book_id))

    def delete_book(self, book_id: int):
        self._execute("DELETE FROM books WHERE id=%s", (book_id,))

# ---------------statistics---------------

    def stats_by_title(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT title, COUNT(*) as count FROM books GROUP BY title ORDER BY count DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["title", "count"])
    
    def stats_by_author(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT author, COUNT(*) as count FROM books GROUP BY author ORDER BY count DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["author", "count"])

    def stats_by_language(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT language, COUNT(*) as count FROM books GROUP BY language ORDER BY count DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["language", "count"])

    def stats_by_year(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT publication_year, COUNT(*) as count FROM books WHERE publication_year IS NOT NULL GROUP BY publication_year ORDER BY publication_year"
            , fetch=True)
        return pd.DataFrame(rows, columns=["year", "count"])
    
    def stats_by_publisher(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT publisher, COUNT(*) as count FROM books WHERE publisher IS NOT NULL GROUP BY publisher ORDER BY count DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["publisher", "count"])
    
    def stats_by_city(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT city, COUNT(*) as count FROM books WHERE city IS NOT NULL GROUP BY city ORDER BY count DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["city", "count"])
    
    def stats_by_stile(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT stile, COUNT(*) as count FROM books WHERE stile IS NOT NULL GROUP BY stile ORDER BY count DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["stile", "count"])
    
    def stats_by_stile_percent(self) -> pd.DataFrame:
        rows = self._execute(
            "SELECT stile, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM books WHERE stile IS NOT NULL), 1) as percent FROM books WHERE stile IS NOT NULL GROUP BY stile ORDER BY percent DESC",
            fetch=True
        )
        return pd.DataFrame(rows, columns=["stile", "percent"])