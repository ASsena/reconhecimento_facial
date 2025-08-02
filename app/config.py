import mysql.connector

# Configuração da conexão com o MySQL
db_connection = mysql.connector.connect(
    host="localhost",  # ou o endereço do servidor
    user="root",
    password="",
    database="eureka_reconhecimento_facial"
)

# config.py

DB_CONFIG = {
    "host" : "localhost",  # ou o endereço do servidor
    "user" : "root",
    "password" : "",
    "database" : "eureka_reconhecimento"
}


cursor = db_connection.cursor()

# Executando uma consulta para verificar a conexão
cursor.execute("SELECT DATABASE()")
database_name = cursor.fetchone()
print(f"Conectado ao banco de dados: {database_name}")



# Usando o banco de dados
cursor.execute("USE eureka_reconhecimento")



