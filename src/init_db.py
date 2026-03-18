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

def create_tables():
    commands = (
        """
        CREATE TABLE IF NOT EXISTS items (
            itemID SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(500) NOT NULL,
            type VARCHAR(50) NOT NULL,
            material BOOLEAN NOT NULL,
            statsID INTEGER NOT NULL,
            sellPrice INTEGER NOT NULL,
            CONSTRAINT fk_item_recipie
                FOREIGN KEY(statsID)
                REFERENCES stats(statID)
                ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS itemsRecipies (
            itemRecipieID SERIAL PRIMARY KEY,
            itemID INTEGER NOT NULL,
            craftingStation VARCHAR(50),
            CONSTRAINT fk_item_recipie
                FOREIGN KEY(itemID)
                REFERENCES items(itemID)
                ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recipies (
            recipieID SERIAL PRIMARY KEY,
            itemRecipieID INTEGER NOT NULL,
            itemID INTEGER NOT NULL,
            amount INTEGER DEFAULT(1),
            CONSTRAINT fk_item_recipie_link
                FOREIGN KEY(itemRecipieID)
                REFERENCES itemsRecipies(itemRecipieID)
                ON DELETE CASCADE,
            CONSTRAINT fk_item_ingredient
                FOREIGN KEY(itemID)
                REFERENCES items(itemID)
                ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS stats (
            statID SERIAL PRIMARY KEY,
            itemID INTEGER NOT NULL,
            damage VARCHAR(20),
            knockback VARCHAR(20),
            criticalChance VARCHAR(20),
            useTime VARCHAR(20),
            mana VARCHAR(20),
            velocity VARCHAR(20),
            tooltip VARCHAR(100),
            defense VARCHAR(20),
            setBonus VARCHAR(100),
            bodySlot VARCHAR(50),
            CONSTRAINT fk_item_recipie
                FOREIGN KEY(itemID)
                REFERENCES items(itemID)
                ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS enemy (
            enemyID SERIAL PRIMARY KEY,

            
        )
        """
    )
    
    
    conn = None
    try:
        # Połączenie z bazą
        conn = psycopg2.connect(**DB_CONFIG)
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
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    create_tables()
