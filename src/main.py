import os
import time
import logging

import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2 import OperationalError as PostgresError
import redis
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure as MongoError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_mysql():
    host = os.environ.get('MYSQL_HOST', 'mysql')
    user = os.environ.get('MYSQL_USER', 'user')
    password = os.environ.get('MYSQL_PASSWORD', 'password')
    database = os.environ.get('MYSQL_DATABASE', 'mydatabase')
    
    retries = 30
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
    host = os.environ.get('POSTGRES_HOST', 'postgres')
    user = os.environ.get('POSTGRES_USER', 'user')
    password = os.environ.get('POSTGRES_PASSWORD', 'password')
    database = os.environ.get('POSTGRES_DB', 'mydatabase')

    retries = 30
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
    host = os.environ.get('REDIS_HOST', 'redis')
    password = os.environ.get('REDIS_PASSWORD', 'password')
    
    retries = 30
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
    host = os.environ.get('MONGO_HOST', 'mongodb')
    user = os.environ.get('MONGO_USER', 'user')
    password = os.environ.get('MONGO_PASSWORD', 'password')
    
    uri = f"mongodb://{user}:{password}@{host}:27017/"
    retries = 30
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

def init_postgres(conn):
    try:
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
    
    # Connect to all databases
    mysql_conn = wait_for_mysql()
    postgres_conn = wait_for_postgres()
    redis_conn = wait_for_redis()
    mongo_client = wait_for_mongo()
    
    # Initialize structures and data
    init_mysql(mysql_conn)
    init_postgres(postgres_conn)
    init_redis(redis_conn)
    init_mongo(mongo_client)
    
    # Close connections
    mysql_conn.close()
    postgres_conn.close()
    mongo_client.close()
    
    logging.info("Database initialization completed successfully!")
    
    # Keep the container running
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()