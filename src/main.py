import os
import time
import logging

import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2 import OperationalError as PostgresError
import redis

import init_db
import generate_data
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure as MongoError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_mysql():
    host = os.environ.get('MYSQL_HOST', 'localhost')
    user = os.environ.get('MYSQL_USER', 'user')
    password = os.environ.get('MYSQL_PASSWORD', 'password')
    database = os.environ.get('MYSQL_DATABASE', 'mydatabase')
    
    retries = 150
    while retries > 0:
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if conn.is_connected():
                logging.info("Successfully connected to MySQL")
                return conn
        except MySQLError as e:
            logging.warning(f"Waiting for MySQL... ({e})")
        retries -= 1
        time.sleep(2)
    raise Exception("Could not connect to MySQL after multiple retries")

def wait_for_postgres():
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    user = os.environ.get('POSTGRES_USER', 'user')
    password = os.environ.get('POSTGRES_PASSWORD', 'password')
    database = os.environ.get('POSTGRES_DB', 'mydatabase')

    retries = 150
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=database
            )
            logging.info("Successfully connected to PostgreSQL")
            return conn
        except PostgresError as e:
            logging.warning(f"Waiting for PostgreSQL... ({e})")
        retries -= 1
        time.sleep(2)
    raise Exception("Could not connect to PostgreSQL after multiple retries")

def wait_for_redis():
    host = os.environ.get('REDIS_HOST', 'localhost')
    password = os.environ.get('REDIS_PASSWORD', 'password')
    
    retries = 150
    while retries > 0:
        try:
            r = redis.Redis(host=host, port=6379, password=password, db=0, decode_responses=True)
            if r.ping():
                logging.info("Successfully connected to Redis")
                return r
        except redis.ConnectionError as e:
            logging.warning(f"Waiting for Redis... ({e})")
        retries -= 1
        time.sleep(2)
    raise Exception("Could not connect to Redis after multiple retries")

def wait_for_mongo():
    host = os.environ.get('MONGO_HOST', 'localhost')
    user = os.environ.get('MONGO_USER', 'user')
    password = os.environ.get('MONGO_PASSWORD', 'password')
    
    uri = f"mongodb://{user}:{password}@{host}:27017/"
    retries = 150
    while retries > 0:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            logging.info("Successfully connected to MongoDB")
            return client
        except MongoError as e:
            logging.warning(f"Waiting for MongoDB... ({e})")
        retries -= 1
        time.sleep(2)
    raise Exception("Could not connect to MongoDB after multiple retries")

def init_mysql(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_mysql (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data if the table is empty
        cursor.execute("SELECT COUNT(*) FROM users_mysql")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO users_mysql (username, email) VALUES (%s, %s)", ('mysql_user', 'user@mysql.local'))
            conn.commit()
            logging.info("Inserted sample data into users_mysql")
        else:
            logging.info("users_mysql table already contains data")
            
        cursor.close()
    except Exception as e:
        logging.error(f"Error initializing MySQL: {e}")

def init_postgres_and_mysql_schemas(pg_conn, mysql_conn):
    try:
        # Run the full schema initialization from init_db.py for both PG and MySQL
        logging.info("Running init_db schema initialization for PostgreSQL and MySQL...")
        init_db.create_tables(pg_conn, mysql_conn)
        
        # Initialize users_postgres
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_postgres (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data if the table is empty
        cursor.execute("SELECT COUNT(*) FROM users_postgres")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO users_postgres (username, email) VALUES (%s, %s)", ('postgres_user', 'user@postgres.local'))
            conn.commit()
            logging.info("Inserted sample data into users_postgres")
        else:
            logging.info("users_postgres table already contains data")
            
        cursor.close()
        logging.info("PostgreSQL initialization complete.")
    except Exception as e:
        logging.error(f"Error initializing PostgreSQL: {e}")
        conn.rollback()

def init_redis(r):
    try:
        if not r.exists('app_status'):
            r.set('app_status', 'initialized')
            r.set('sample_user:1', '{"username": "redis_user", "email": "user@redis.local"}')
            logging.info("Inserted sample data into Redis")
        else:
            logging.info("Redis already initialized")
    except Exception as e:
        logging.error(f"Error initializing Redis: {e}")

def init_mongo(client):
    try:
        db = client['mydatabase']
        collection = db['users_mongo']
        
        if collection.count_documents({}) == 0:
            collection.insert_one({
                "username": "mongo_user",
                "email": "user@mongo.local",
                "status": "active"
            })
            logging.info("Inserted sample data into users_mongo")
        else:
            logging.info("MongoDB users_mongo collection already contains data")
    except Exception as e:
        logging.error(f"Error initializing MongoDB: {e}")

def main():
    logging.info("Starting database initialization script...")
    
    mysql_conn = wait_for_mysql()
    postgres_conn = wait_for_postgres()
    redis_conn = wait_for_redis()
    mongo_client = wait_for_mongo()
    
    init_mysql(mysql_conn)
    init_postgres_and_mysql_schemas(postgres_conn, mysql_conn)
    
    # Initialize users_postgres manually
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_postgres (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM users_postgres")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users_postgres (username, email) VALUES (%s, %s)", ('postgres_user', 'user@postgres.local'))
            postgres_conn.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"Error initializing users_postgres: {e}")
        postgres_conn.rollback()

    init_redis(redis_conn)
    init_mongo(mongo_client)
    
    profile = os.environ.get('PROFILE', 'maly')
    logging.info(f"Starting bulk data generation with profile: {profile}...")
    start_time = time.time()
    try:
        generate_data.run_sync(profile)
    except Exception as e:
        logging.error(f"Error during bulk data generation: {e}")
    end_time = time.time()
    logging.info(f"Bulk data generation finished in {end_time - start_time:.2f} seconds.")

    logging.info("Verifying row counts across databases...")
    for table, target_count in generate_data.COUNTS.items():
        # Postgres
        try:
            with postgres_conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = cur.fetchone()[0]
                if pg_count < target_count:
                    logging.warning(f"Postgres '{table}' count mismatch: found {pg_count}, expected >= {target_count}")
        except Exception as e:
            logging.error(f"Postgres verification error on {table}: {e}")
            postgres_conn.rollback()

        # MySQL
        try:
            with mysql_conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                my_count = cur.fetchone()[0]
                if my_count < target_count:
                    logging.warning(f"MySQL '{table}' count mismatch: found {my_count}, expected >= {target_count}")
        except Exception as e:
            logging.error(f"MySQL verification error on {table}: {e}")

        # Mongo
        try:
            mongo_count = mongo_client['mydatabase'][table].count_documents({})
            if mongo_count < target_count:
                logging.warning(f"Mongo '{table}' count mismatch: found {mongo_count}, expected >= {target_count}")
        except Exception as e:
            logging.error(f"Mongo verification error on {table}: {e}")

    # Redis Verification (Global count instead of keys * per table to save memory)
    try:
        redis_size = redis_conn.dbsize()
        expected_redis_size = sum(generate_data.COUNTS.values())
        if redis_size < expected_redis_size:
            logging.warning(f"Redis TOTAL size mismatch: found {redis_size}, expected >= {expected_redis_size}")
    except Exception as e:
        logging.error(f"Redis size check error: {e}")

    logging.info("Verification complete.")

    logging.info("Flushing and saving all databases to disk to ensure durability...")
    
    # 2. Redis memory to disk dump
    try:
        redis_conn.bgsave()
        logging.info("- Redis triggered BGSAVE (saving to dump.rdb).")
    except Exception as e:
        # Prevent throwing if a bgsave is already in progress
        logging.warning(f"- Redis bgsave note: {e}")

    # 3. Mongo memory to disk flush
    try:
        mongo_client.admin.command('fsync')
        logging.info("- MongoDB data forcefully synced (fsync) to disk.")
    except Exception as e:
        logging.warning(f"- Mongo fsync note: {e}")

    mysql_conn.close()
    postgres_conn.close()
    mongo_client.close()
    
    logging.info("Database initialization and synchronization completed successfully!")
    
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()