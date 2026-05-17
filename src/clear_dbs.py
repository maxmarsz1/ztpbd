import os
import sys
import logging
import psycopg2
import mysql.connector
import redis
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_configs():
    return {
        'mysql': {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'user': os.environ.get('MYSQL_USER', 'user'),
            'password': os.environ.get('MYSQL_PASSWORD', 'password'),
            'database': os.environ.get('MYSQL_DATABASE', 'mydatabase'),
            'port': int(os.environ.get('MYSQL_PORT', 3306))
        },
        'postgres': {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'user': os.environ.get('POSTGRES_USER', 'user'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'password'),
            'dbname': os.environ.get('POSTGRES_DB', 'mydatabase'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432))
        },
        'redis': {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', 6379)),
            'password': os.environ.get('REDIS_PASSWORD', 'password')
        },
        'mongo': {
            'host': os.environ.get('MONGO_HOST', 'localhost'),
            'port': int(os.environ.get('MONGO_PORT', 27017)),
            'user': os.environ.get('MONGO_USER', 'user'),
            'password': os.environ.get('MONGO_PASSWORD', 'password')
        }
    }

def clear_dbs():
    cfg = get_db_configs()
    logging.info("Rozpoczęto czyszczenie baz danych...")

    # PostgreSQL
    try:
        logging.info("Czyszczenie PostgreSQL...")
        pg_conn = psycopg2.connect(**cfg['postgres'])
        with pg_conn.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        pg_conn.commit()
        pg_conn.close()
        logging.info("Sukces: PostgreSQL (usunięto schemat i zrekonstruowano pusty).")
    except Exception as e:
        logging.error(f"Błąd PostgreSQL: {e}")

    # MySQL
    try:
        logging.info("Czyszczenie MySQL...")
        my_conn = mysql.connector.connect(**cfg['mysql'])
        with my_conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS=0;")
            cur.execute("SHOW TABLES;")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                cur.execute(f"DROP TABLE IF EXISTS {t}")
            cur.execute("SET FOREIGN_KEY_CHECKS=1;")
        my_conn.commit()
        my_conn.close()
        logging.info(f"Sukces: MySQL (usunięto {len(tables)} tabel).")
    except Exception as e:
        logging.error(f"Błąd MySQL: {e}")

    # Redis
    try:
        logging.info("Czyszczenie Redis...")
        r = redis.Redis(
            host=cfg['redis']['host'],
            port=cfg['redis']['port'],
            password=cfg['redis']['password'],
            decode_responses=True
        )
        r.flushall()
        logging.info("Sukces: Redis (wykonano flushall - całkowite czyszczenie).")
    except Exception as e:
        logging.error(f"Błąd Redis: {e}")

    # MongoDB
    try:
        logging.info("Czyszczenie MongoDB...")
        mongo_uri = f"mongodb://{cfg['mongo']['user']}:{cfg['mongo']['password']}@{cfg['mongo']['host']}:{cfg['mongo']['port']}/"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.drop_database('mydatabase')
        logging.info("Sukces: MongoDB (całkowicie usunięto bazę 'mydatabase').")
    except Exception as e:
        logging.error(f"Błąd MongoDB: {e}")

    logging.info("Czyszczenie zakończone. Uruchom 'python init_db.py', aby stworzyć puste tabele na nowo.")

if __name__ == "__main__":
    print("=" * 60)
    print(" UWAGA: Ten skrypt bezpowrotnie kasuje wszystkie dane z 4 baz!")
    print("=" * 60)
    confirm = input("Czy na pewno chcesz usunąć wszystko? (T/N): ")
    if confirm.strip().lower() in ['t', 'tak', 'y', 'yes']:
        clear_dbs()
    else:
        print("Anulowano.")
