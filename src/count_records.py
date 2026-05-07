import os
import sys
import logging

from main import wait_for_mysql, wait_for_postgres, wait_for_redis, wait_for_mongo

# Wyłączenie logów informacyjnych z main.py, aby nie zaśmiecały tabeli wyników
logging.getLogger().setLevel(logging.ERROR)

TABLES = [
    'Environments', 'AITypes', 'NPCs', 'NPCEnvironments', 
    'EnemyVariants', 'EnemyVariantStats', 'NPCSounds', 
    'Stats', 'Items', 'itemsRecipies', 'recipies', 'EnemyDrops'
]

def print_row(db_name, table_name, count):
    print(f"{db_name:<15} | {table_name:<20} | {count:>15}")

def main():
    print("Nawiązywanie połączeń z bazami danych... (Proszę czekać)")
    try:
        mysql_conn = wait_for_mysql()
    except Exception as e:
        mysql_conn = None
        print(f"MySQL error: {e}")

    try:
        pg_conn = wait_for_postgres()
    except Exception as e:
        pg_conn = None
        print(f"PostgreSQL error: {e}")

    try:
        redis_conn = wait_for_redis()
    except Exception as e:
        redis_conn = None
        print(f"Redis error: {e}")

    try:
        mongo_client = wait_for_mongo()
        mongo_db = mongo_client['mydatabase']
    except Exception as e:
        mongo_client = None
        print(f"MongoDB error: {e}")

    print("\n" + "="*56)
    print(f"{'BAZA DANYCH':<15} | {'TABELA':<20} | {'LICZBA REKORDÓW':>15}")
    print("="*56)

    totals = {
        'MySQL': 0,
        'PostgreSQL': 0,
        'MongoDB': 0,
        'Redis': 0
    }

    # MySQL
    if mysql_conn:
        with mysql_conn.cursor() as cur:
            for table in TABLES:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    totals['MySQL'] += count
                    print_row("MySQL", table, count)
                except Exception as e:
                    print_row("MySQL", table, "BŁĄD")
        mysql_conn.close()

    print("-" * 56)

    # PostgreSQL
    if pg_conn:
        with pg_conn.cursor() as cur:
            for table in TABLES:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    totals['PostgreSQL'] += count
                    print_row("PostgreSQL", table, count)
                except Exception as e:
                    print_row("PostgreSQL", table, "BŁĄD")
                    pg_conn.rollback()
        pg_conn.close()

    print("-" * 56)

    # MongoDB
    if mongo_client:
        for table in TABLES:
            try:
                count = mongo_db[table].count_documents({})
                totals['MongoDB'] += count
                print_row("MongoDB", table, count)
            except Exception as e:
                print_row("MongoDB", table, "BŁĄD")
        mongo_client.close()

    print("-" * 56)

    # Redis
    if redis_conn:
        try:
            # W bazie klucz-wartość jak Redis, zliczanie kluczy po prefixach
            # metodą SCAN (np. SCAN 0 MATCH Items:*) potrafi trwać minuty przy
            # wielu milionach kluczy, a nawet zawiesić na ułamek czasu serwer Redis.
            # Z tego powodu, do sprawdzenia czy dane się załadowały, wykorzystujemy
            # komendę DBSIZE, która w Redisie odpowiada O(1) i jest błyskawiczna.
            total_redis = redis_conn.dbsize()
            totals['Redis'] = total_redis
            
            print_row("Redis", "WSZYSTKIE TABELE", "---")
            print_row("Redis", "(Suma kluczy)", total_redis)
        except Exception as e:
             print_row("Redis", "BŁĄD", "-")
        redis_conn.close()

    print("="*56)
    print("PODSUMOWANIE - CAŁKOWITA SUMA REKORDÓW W BAZACH:")
    for db_name, total in totals.items():
        # Używamy separatora tysięcy ułatwiającego czytanie
        print(f" -> {db_name:<15}: {total:,}".replace(',', ' '))
    print("="*56)

if __name__ == '__main__':
    main()
