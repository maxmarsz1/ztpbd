import psycopg2
import mysql.connector
import redis
from pymongo import MongoClient

def reset_all_databases():
    tables_to_drop = [
        'EnemyDrops', 'recipies', 'itemsRecipies', 'Items', 'Stats',
        'NPCSounds', 'EnemyVariantStats', 'EnemyVariants',
        'NPCEnvironments', 'NPCs', 'AITypes', 'Environments'
    ]

    print("Resetowanie PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(dbname="mydatabase", user="user", password="password", host="localhost", port="5432")
        cur = pg_conn.cursor()
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        pg_conn.commit()
        cur.close()
        pg_conn.close()
        print("PostgreSQL zresetowany.")
    except Exception as e:
        print(f"Błąd PG: {e}")

    print("Resetowanie MySQL...")
    try:
        my_conn = mysql.connector.connect(database="mydatabase", user="user", password="password", host="localhost", port="3306")
        cur = my_conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table};")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        my_conn.commit()
        cur.close()
        my_conn.close()
        print("MySQL zresetowany.")
    except Exception as e:
        print(f"Błąd MySQL: {e}")

    print("Resetowanie Redis...")
    try:
        r = redis.Redis(host='localhost', port=6379, password='password', db=0)
        r.flushdb()
        print("Redis zresetowany.")
    except Exception as e:
        print(f"Błąd Redis: {e}")

    print("Resetowanie MongoDB...")
    try:
        mongo = MongoClient("mongodb://user:password@localhost:27017/")
        db = mongo['mydatabase']
        for table in tables_to_drop:
            db[table].drop()
        print("MongoDB zresetowane.")
    except Exception as e:
        print(f"Błąd MongoDB: {e}")

if __name__ == '__main__':
    reset_all_databases()
