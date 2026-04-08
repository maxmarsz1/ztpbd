import os
import time
import logging
import random
from faker import Faker
import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
import psycopg2.extras
import psycopg2.pool
import mysql.connector
from mysql.connector import pooling
import redis
import pymongo
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK_SIZE = 50000

COUNTS = {
    'Environments': 100,
    'AITypes': 100,
    'NPCs': 1000000,
    'NPCEnvironments': 1000000,
    'EnemyVariants': 1000000,
    'EnemyVariantStats': 1000000,
    'NPCSounds': 100000,
    'Stats': 2500000,
    'Items': 2500000,
    'itemsRecipies': 3000000,
    'recipies': 3000000,
    'EnemyDrops': 1000000
}

fake = Faker()

print("Pre-generating Faker pools for realistic data...")
POOL_WORDS = [fake.word().title() for _ in range(500)]
POOL_SENTS = [fake.text(max_nb_chars=90).replace('\n', ' ') for _ in range(500)]
POOL_URLS = [fake.url() for _ in range(200)]
POOL_CRAFT = ["Work Bench", "Furnace", "Anvil", "Loom", "Sawmill", "Tinker's Workshop"]

def get_db_configs():
    return {
        'mysql': {
            'host': os.environ.get('MYSQL_HOST', 'mysql'),
            'user': os.environ.get('MYSQL_USER', 'user'),
            'password': os.environ.get('MYSQL_PASSWORD', 'password'),
            'database': os.environ.get('MYSQL_DATABASE', 'mydatabase'),
            'port': int(os.environ.get('MYSQL_PORT', 3306))
        },
        'postgres': {
            'host': os.environ.get('POSTGRES_HOST', 'postgres'),
            'user': os.environ.get('POSTGRES_USER', 'user'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'password'),
            'dbname': os.environ.get('POSTGRES_DB', 'mydatabase'),
            'port': int(os.environ.get('POSTGRES_PORT', 5432))
        },
        'redis': {
            'host': os.environ.get('REDIS_HOST', 'redis'),
            'password': os.environ.get('REDIS_PASSWORD', 'password'),
            'port': int(os.environ.get('REDIS_PORT', 6379))
        },
        'mongo': {
            'host': os.environ.get('MONGO_HOST', 'mongodb'),
            'user': os.environ.get('MONGO_USER', 'user'),
            'password': os.environ.get('MONGO_PASSWORD', 'password'),
            'port': int(os.environ.get('MONGO_PORT', 27017))
        }
    }

def _get_generator_for_table(table_name, start_id, end_id):
    rows = []
    for i in range(start_id, end_id + 1):
        if table_name == 'Environments':
            rows.append((i, f"{random.choice(POOL_WORDS)} Biome", random.choice(POOL_SENTS)))
        elif table_name == 'AITypes':
            rows.append((i, f"{random.choice(['Fighter', 'Slime', 'Caster', 'Flier', 'Worm'])} AI", random.choice(POOL_SENTS)))
        elif table_name == 'NPCs':
            rows.append((i, i % 100))
        elif table_name == 'NPCEnvironments':
            rows.append((i, (i % COUNTS['NPCs']) + 1, (i % 100) + 1))
        elif table_name == 'EnemyVariants':
            rows.append((i, (i % COUNTS['NPCs']) + 1, (i % 100) + 1, random.choice(["Enemy", "Critter", "TownNPC"]), random.choice(["classic", "expert", "master"])))
        elif table_name == 'EnemyVariantStats':
            rows.append((i, (i % COUNTS['EnemyVariants']) + 1, random.randint(10, 5000), random.randint(5, 100), random.randint(0, 50), random.randint(0, 10000)))
        elif table_name == 'NPCSounds':
            rows.append((i, (i % COUNTS['NPCs']) + 1, random.choice(POOL_URLS) + f"{i}.wav"))
        elif table_name == 'Stats':
            item_id = (i % COUNTS['Items']) + 1
            rows.append((i, item_id, random.randint(1, 100), random.randint(0, 10), random.randint(4, 100), random.randint(10, 60), random.randint(0, 50), random.randint(1, 15), random.choice(POOL_SENTS), random.randint(0, 20), random.choice(["None", "Stat Bonus", "Aura"]), random.choice(["Weapon", "Armor", "Accessory", "None"])))
        elif table_name == 'Items':
            stat_id = (i % COUNTS['Stats']) + 1
            rows.append((i, f"{random.choice(POOL_WORDS)} {random.choice(['Sword', 'Shield', 'Bow', 'Staff', 'Helmet', 'Ingot'])} {i}", random.choice(POOL_SENTS), random.choice(["Weapon", "Material", "Consumable", "Accessory"]), random.choice([True, False]), stat_id, random.randint(10, 50000)))
        elif table_name == 'itemsRecipies':
            item_id = (i % COUNTS['Items']) + 1
            rows.append((i, item_id, random.choice(POOL_CRAFT)))
        elif table_name == 'recipies':
            recipie_id = (i % COUNTS['itemsRecipies']) + 1
            item_id = (i % COUNTS['Items']) + 1
            rows.append((i, recipie_id, item_id, random.randint(1, 99)))
        elif table_name == 'EnemyDrops':
            variant_id = (i % COUNTS['EnemyVariants']) + 1
            item_id = (i % COUNTS['Items']) + 1
            rows.append((i, variant_id, item_id, round(random.uniform(0.01, 1.0), 2)))
    return rows

def get_insert_sql(table_name):
    columns_map = {
        'Environments': ("id, name, description", 3),
        'AITypes': ("id, name, description", 3),
        'NPCs': ("id, typeID", 2),
        'NPCEnvironments': ("id, npcID, environmentID", 3),
        'EnemyVariants': ("id, npcID, AITypeID, type, mode", 5),
        'EnemyVariantStats': ("id, variantID, health, damage, defense, coins", 6),
        'NPCSounds': ("id, npcID, url", 3),
        'Stats': ("id, itemID, damage, knockback, criticalChance, useTime, mana, velocity, tooltip, defense, setBonus, bodySlot", 12),
        'Items': ("id, name, description, type, material, statsID, sellPrice", 7),
        'itemsRecipies': ("id, itemID, craftingStation", 3),
        'recipies': ("id, itemRecipieID, itemID, amount", 4),
        'EnemyDrops': ("id, variantID, itemID, rate", 4),
    }
    cols, num_args = columns_map[table_name]
    placeholders = ", ".join(["%s"] * num_args)
    return f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", f"INSERT INTO {table_name} ({cols}) VALUES %s"

def get_mongo_dicts(table_name, rows):
    columns_map = {
        'Environments': ["id", "name", "description"],
        'AITypes': ["id", "name", "description"],
        'NPCs': ["id", "typeID"],
        'NPCEnvironments': ["id", "npcID", "environmentID"],
        'EnemyVariants': ["id", "npcID", "AITypeID", "type", "mode"],
        'EnemyVariantStats': ["id", "variantID", "health", "damage", "defense", "coins"],
        'NPCSounds': ["id", "npcID", "url"],
        'Stats': ["id", "itemID", "damage", "knockback", "criticalChance", "useTime", "mana", "velocity", "tooltip", "defense", "setBonus", "bodySlot"],
        'Items': ["id", "name", "description", "type", "material", "statsID", "sellPrice"],
        'itemsRecipies': ["id", "itemID", "craftingStation"],
        'recipies': ["id", "itemRecipieID", "itemID", "amount"],
        'EnemyDrops': ["id", "variantID", "itemID", "rate"],
    }
    cols = columns_map[table_name]
    return [dict(zip(cols, row)) for row in rows]

def process_chunk_unified(my_pool, pg_pool, redis_client, mongo_client, table, start_offset, end_val, my_sql, pg_sql):
    rows = _get_generator_for_table(table, start_offset + 1, end_val)
    
    # 1. MySQL
    if my_pool:
        try:
            conn = my_pool.get_connection()
            cur = conn.cursor()
            cur.execute("SET SESSION unique_checks = 0;")
            cur.execute("SET SESSION foreign_key_checks = 0;")
            cur.executemany(my_sql.replace("INSERT INTO", "REPLACE INTO"), rows)
            conn.commit()
            cur.close()
        except Exception as e:
            logging.error(f"Batch insert error MySQL on {table}: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                conn.close()

    # 2. Postgres
    if pg_pool:
        try:
            conn = pg_pool.getconn()
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, pg_sql + " ON CONFLICT (id) DO NOTHING", rows)
            conn.commit()
        except Exception as e:
            logging.error(f"Batch insert error Postgres on {table}: {e}")
            if 'conn' in locals(): conn.rollback()
        finally:
            if 'conn' in locals(): pg_pool.putconn(conn)
            
    # Cache mapping for NoSQL
    mongo_dicts = None
    if redis_client or mongo_client:
        mongo_dicts = get_mongo_dicts(table, rows)

    # 3. Redis
    if redis_client:
        try:
            pipe = redis_client.pipeline(transaction=False)
            for d in mongo_dicts:
                key = f"{table}:{d['id']}"
                pipe.hset(key, mapping={k: str(v) for k, v in d.items()})
            pipe.execute()
        except Exception as e:
            logging.error(f"Batch insert error Redis on {table}: {e}")

    # 4. Mongo
    if mongo_client:
        try:
            m_dicts = []
            for d in mongo_dicts:
                md = d.copy()
                md['_id'] = md.pop('id')
                m_dicts.append(md)
            mongo_client['mydatabase'][table].insert_many(m_dicts, ordered=False)
        except pymongo.errors.BulkWriteError:
            pass # DO NOTHING equivalent for duplicate keys
        except Exception as e:
            logging.error(f"Batch insert error Mongo on {table}: {e}")

def run_sync():
    cfg = get_db_configs()
    my_pool, pg_pool, redis_client, mongo_client = None, None, None, None
    
    # Init Connections
    try:
        my_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=16, **cfg['mysql'])
        logging.info("[Unified Core] MySQL connected.")
    except Exception as e:
        logging.warning("[Unified Core] Skipping MySQL.")

    try:
        pg_pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=16, **cfg['postgres'])
        logging.info("[Unified Core] PostgreSQL connected.")
        
        # Postgres requires dropping constraints dynamically to bulk load wildly without topological sorts
        temp_conn = pg_pool.getconn()
        with temp_conn.cursor() as cur:
            cur.execute("ALTER TABLE Stats DROP CONSTRAINT IF EXISTS fk_stats_item")
        temp_conn.commit()
        pg_pool.putconn(temp_conn)
    except Exception as e:
        logging.warning("[Unified Core] Skipping PostgreSQL.")

    try:
        redis_client = redis.Redis(host=cfg['redis']['host'], port=cfg['redis']['port'], password=cfg['redis']['password'], decode_responses=True, max_connections=32)
        redis_client.ping()
        logging.info("[Unified Core] Redis connected.")
    except Exception as e:
        logging.warning("[Unified Core] Skipping Redis.")
        redis_client = None

    try:
        mongo_uri = f"mongodb://{cfg['mongo']['user']}:{cfg['mongo']['password']}@{cfg['mongo']['host']}:{cfg['mongo']['port']}/"
        mongo_client = MongoClient(mongo_uri, maxPoolSize=100)
        mongo_client.admin.command('ping')
        logging.info("[Unified Core] MongoDB connected.")
    except Exception as e:
        logging.warning("[Unified Core] Skipping MongoDB.")
        mongo_client = None

    tables = [
        'Environments', 'AITypes', 'NPCs', 'NPCEnvironments', 
        'EnemyVariants', 'EnemyVariantStats', 'NPCSounds', 
        'Stats', 'Items', 'itemsRecipies', 'recipies', 'EnemyDrops'
    ]

    for table in tables:
        target_count = COUNTS[table]
        logging.info(f"--- Starting Unified Table {table} ({target_count} rows) ---")
        
        my_sql, pg_sql = get_insert_sql(table)

        # Smart Unified Resuming
        # Calculates the lowest completed watermark across all 4 databases safely
        active_maxes = []
        if my_pool:
            try:
                conn = my_pool.get_connection()
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                    active_maxes.append(cur.fetchone()[0])
                conn.close()
            except: pass
        if pg_pool:
            try:
                conn = pg_pool.getconn()
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                    active_maxes.append(cur.fetchone()[0])
                pg_pool.putconn(conn)
            except: pass
        if redis_client:
            loc = 0
            for offset in range(target_count - CHUNK_SIZE, -1, -CHUNK_SIZE):
                if redis_client.exists(f"{table}:{offset + CHUNK_SIZE}"):
                    loc = offset + CHUNK_SIZE
                    break
            active_maxes.append(loc)
        if mongo_client:
            try:
                top = mongo_client['mydatabase'][table].find_one({}, sort=[("_id", -1)])
                active_maxes.append(top['_id'] if top else 0)
            except: pass

        # Begin at the slowest database's last completed chunk, or 0
        global_start = min(active_maxes) if active_maxes else 0
        global_start = (global_start // CHUNK_SIZE) * CHUNK_SIZE

        if global_start >= target_count:
            logging.info(f"Skipping {table} - thoroughly populated across all active DBs.")
            continue
            
        if global_start > 0:
            logging.info(f"Resuming {table} globally from row {global_start}...")

        start_time = time.time()
        
        futures = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            for offset in range(global_start, target_count, CHUNK_SIZE):
                end_val = min(offset + CHUNK_SIZE, target_count)
                f = executor.submit(process_chunk_unified, my_pool, pg_pool, redis_client, mongo_client, table, offset, end_val, my_sql, pg_sql)
                futures.append(f)
            
            for f in tqdm.tqdm(as_completed(futures), total=len(futures), desc=f"Unified Ingestion {table} [Threads: 16]"):
                f.result() 

        logging.info(f"Finished {table} in {time.time() - start_time:.2f} seconds")

    # Restore Postgres constraints at the absolute end
    if pg_pool:
        try:
            conn = pg_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE Stats ADD CONSTRAINT fk_stats_item FOREIGN KEY (itemID) REFERENCES Items(id) DEFERRABLE INITIALLY DEFERRED")
            conn.commit()
            pg_pool.putconn(conn)
        except: pass
        pg_pool.closeall()
        
    if mongo_client: mongo_client.close()
    if redis_client: redis_client.close()

if __name__ == '__main__':
    run_sync()
