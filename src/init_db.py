import psycopg2
from psycopg2 import sql

# Konfiguracja połączenia (zgodna z docker-compose.yml)
DB_CONFIG = {
    "dbname": "mydatabase",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

def create_tables(conn=None):
    commands = (
        """
        CREATE TABLE Environments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            description TEXT
        )
        """,
        """
        CREATE TABLE AITypes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            description TEXT
        )
        """,
        """
        CREATE TABLE NPCs (
            id SERIAL PRIMARY KEY,
            typeID INTEGER
        )
        """,
        """
        CREATE TABLE NPCEnvironments (
            id SERIAL PRIMARY KEY,
            npcID INTEGER REFERENCES NPCs(id),
            environmentID INTEGER REFERENCES Environments(id)
        )
        """,
        """
        CREATE TABLE EnemyVariants (
            id SERIAL PRIMARY KEY,
            npcID INTEGER REFERENCES NPCs(id),
            AITypeID INTEGER REFERENCES AITypes(id),
            type VARCHAR(50), -- e.g., Enemy/Critter/TownNPC
            mode VARCHAR(50)  -- e.g., classic/expert/master
        )
        """,
        """
        CREATE TABLE EnemyVariantStats (
            id SERIAL PRIMARY KEY,
            variantID INTEGER REFERENCES EnemyVariants(id),
            health INTEGER,
            damage INTEGER,
            defense INTEGER,
            coins INTEGER
        )
        """,
        """
        CREATE TABLE NPCSounds (
            id SERIAL PRIMARY KEY,
            npcID INTEGER REFERENCES NPCs(id),
            url VARCHAR(255)
        )
        """,
        """
        CREATE TABLE Stats (
            id SERIAL PRIMARY KEY,
            itemID INTEGER NOT NULL, -- Foreign key constraint added later
            damage VARCHAR(20),
            knockback VARCHAR(20),
            criticalChance VARCHAR(20),
            useTime VARCHAR(20),
            mana VARCHAR(20),
            velocity VARCHAR(20),
            tooltip VARCHAR(100),
            defense VARCHAR(20),
            setBonus VARCHAR(100),
            bodySlot VARCHAR(50)
        )
        """,
        """
        CREATE TABLE Items (
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
        ALTER TABLE Stats 
        ADD CONSTRAINT fk_stats_item 
        FOREIGN KEY (itemID) REFERENCES Items(id) DEFERRABLE INITIALLY DEFERRED
        """,
        """
        CREATE TABLE itemsRecipies (
            id SERIAL PRIMARY KEY,
            itemID INTEGER NOT NULL REFERENCES Items(id),
            craftingStation VARCHAR(50)
        )
        """,
        """
        CREATE TABLE recipies (
            id SERIAL PRIMARY KEY,
            itemRecipieID INTEGER NOT NULL REFERENCES itemsRecipies(id),
            itemID INTEGER NOT NULL REFERENCES Items(id),
            amount INTEGER DEFAULT 1
        )
        """,
        """
        CREATE TABLE EnemyDrops (
            id SERIAL PRIMARY KEY,
            variantID INTEGER REFERENCES EnemyVariants(id),
            itemID INTEGER REFERENCES Items(id),
            rate DECIMAL -- Assumed DECIMAL or FLOAT for drop rate percentage
        )
        """
    )
    
    
    own_conn = False
    try:
        if conn is None:
            # Połączenie z bazą
            conn = psycopg2.connect(**DB_CONFIG)
            own_conn = True
        
        cur = conn.cursor()
        
        # Tworzenie tabel
        print("Tworzenie tabel i relacji...")
        for command in commands:
            cur.execute(command)
        
        # Zatwierdzenie zmian
        conn.commit()
        cur.close()
        print("Sukces! Tabele zostały utworzone.")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Błąd: {error}")
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if own_conn and conn is not None:
            conn.close()

if __name__ == "__main__":
    create_tables()
