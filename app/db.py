# db.py
import mysql.connector
from app.config import DB_CONFIG


class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print("Conexão bem-sucedida com o banco de dados")
        except mysql.connector.Error as err:
            print(f"Erro ao conectar ao banco de dados: {err}")

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Conexão fechada.")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Erro ao executar a consulta: {err}")

    def fetch_one(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
