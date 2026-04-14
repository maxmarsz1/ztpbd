import psycopg2
import mysql.connector
from psycopg2 import sql

# Konfiguracja połączenia (zgodna z docker-compose.yml)
DB_CONFIG_PG = {
    "dbname": "mydatabase",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

DB_CONFIG_MYSQL = {
    "database": "mydatabase",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "3306"
}

def create_tables(pg_conn=None, mysql_conn=None):
    commands_pg = (
        """
        CREATE TABLE IF NOT EXISTS Environments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            description TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS AITypes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            description TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NPCs (
            id SERIAL PRIMARY KEY,
            typeID INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NPCEnvironments (
            id SERIAL PRIMARY KEY,
            npcID INTEGER REFERENCES NPCs(id),
            environmentID INTEGER REFERENCES Environments(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS EnemyVariants (
            id SERIAL PRIMARY KEY,
            npcID INTEGER REFERENCES NPCs(id),
            AITypeID INTEGER REFERENCES AITypes(id),
            type VARCHAR(50), -- e.g., Enemy/Critter/TownNPC
            mode VARCHAR(50)  -- e.g., classic/expert/master
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS EnemyVariantStats (
            id SERIAL PRIMARY KEY,
            variantID INTEGER REFERENCES EnemyVariants(id),
            health INTEGER,
            damage INTEGER,
            defense INTEGER,
            coins INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NPCSounds (
            id SERIAL PRIMARY KEY,
            npcID INTEGER REFERENCES NPCs(id),
            url VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Stats (
            id SERIAL PRIMARY KEY,
            itemID INTEGER NOT NULL, -- Foreign key constraint added later
            damage INTEGER,
            knockback INTEGER,
            criticalChance INTEGER,
            useTime INTEGER,
            mana INTEGER,
            velocity INTEGER,
            tooltip VARCHAR(100),
            defense INTEGER,
            setBonus VARCHAR(100),
            bodySlot VARCHAR(50)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(500) NOT NULL,
            type VARCHAR(50) NOT NULL,
            material BOOLEAN NOT NULL,
            statsID INTEGER NOT NULL REFERENCES Stats(id),
            sellPrice INTEGER NOT NULL
        )
        """,
        """
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_stats_item'
            ) THEN 
                ALTER TABLE Stats ADD CONSTRAINT fk_stats_item FOREIGN KEY (itemID) REFERENCES Items(id) DEFERRABLE INITIALLY DEFERRED;
            END IF; 
        END $$;
        """,
        """
        CREATE TABLE IF NOT EXISTS itemsRecipies (
            id SERIAL PRIMARY KEY,
            itemID INTEGER NOT NULL REFERENCES Items(id),
            craftingStation VARCHAR(50)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recipies (
            id SERIAL PRIMARY KEY,
            itemRecipieID INTEGER NOT NULL REFERENCES itemsRecipies(id),
            itemID INTEGER NOT NULL REFERENCES Items(id),
            amount INTEGER DEFAULT 1
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS EnemyDrops (
            id SERIAL PRIMARY KEY,
            variantID INTEGER REFERENCES EnemyVariants(id),
            itemID INTEGER REFERENCES Items(id),
            rate DECIMAL -- Assumed DECIMAL or FLOAT for drop rate percentage
        )
        """
    )
    
    commands_mysql = [c.replace("SERIAL PRIMARY KEY", "INT AUTO_INCREMENT PRIMARY KEY").replace("TEXT", "LONGTEXT").replace("VARCHAR", "VARCHAR").replace("DECIMAL", "DECIMAL(10,4)").replace("BOOLEAN", "BOOLEAN") for c in commands_pg if not c.strip().startswith("DO $$")]
    # Remove Postgres specific block
    
    # We will build constraints differently or just depend on the simple tables for MySQL.

    own_pg_conn = False
    try:
        if pg_conn is None:
            # Połączenie z bazą PG
            pg_conn = psycopg2.connect(**DB_CONFIG_PG)
            own_pg_conn = True
        
        cur = pg_conn.cursor()
        
        # Tworzenie tabel PG
        print("Tworzenie tabel i relacji w PostgreSQL...")
        for command in commands_pg:
            cur.execute(command)
        
        # Zatwierdzenie zmian
        pg_conn.commit()
        cur.close()
        print("Sukces! Tabele zostały utworzone w PostgreSQL.")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Błąd PostgreSQL: {error}")
        if pg_conn is not None:
            pg_conn.rollback()
    finally:
        if own_pg_conn and pg_conn is not None:
            pg_conn.close()

    own_mysql_conn = False
    try:
        if mysql_conn is None:
            # Połączenie z bazą MySQL
            mysql_conn = mysql.connector.connect(**DB_CONFIG_MYSQL)
            own_mysql_conn = True
        
        cur = mysql_conn.cursor()
        
        # Tworzenie tabel MySQL
        print("Tworzenie tabel i relacji w MySQL...")
        for command in commands_mysql:
            # MySQL syntax cleanup
            cmd = command.replace("DEFERRABLE INITIALLY DEFERRED", "")
            cur.execute(cmd)
        
        # Odrębne ograniczenie klucza obcego dla MySQL, bo DO $$ nie działa
        try:
            cur.execute("ALTER TABLE Stats ADD CONSTRAINT fk_stats_item FOREIGN KEY (itemID) REFERENCES Items(id);")
        except mysql.connector.Error:
            pass # Already exists or we handle it gracefully

        mysql_conn.commit()
        cur.close()
        print("Sukces! Tabele zostały utworzone w MySQL.")

    except mysql.connector.Error as error:
        print(f"Błąd MySQL: {error}")
    finally:
        if own_mysql_conn and mysql_conn is not None:
            if mysql_conn.is_connected():
                mysql_conn.close()

if __name__ == "__main__":
    create_tables()
