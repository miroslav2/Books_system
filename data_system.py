import psycopg2
import pandas as pd

class Data_system:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="books_data",
            user="postgres",
            password="103103"
        )

        self.cursor = self.conn.cursor()

    def insert_data_apartments(self, name):
        self.cursor.execute("INSERT INTO apartments (name) VALUES (%s)", (name,))
        self.conn.commit()
    
    def get_data_apartments(self):
        self.cursor.execute("SELECT * FROM apartments")
        return self.cursor.fetchall()
    
    def delete_data_apartments(self, name):
        self.cursor.execute("DELETE FROM apartments WHERE name = (%s)", (name,))
        self.conn.commit()

