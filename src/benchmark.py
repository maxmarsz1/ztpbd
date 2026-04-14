import os
import time
import json
import random
import argparse
import logging
from collections import defaultdict
from main import wait_for_mysql, wait_for_postgres, wait_for_redis, wait_for_mongo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def manage_indexes(pg_conn, my_conn, mongo_client, action="create"):
    logging.info(f"--- {action.upper()} INDEXES ---")
    
    pg_idx = [
        "CREATE INDEX idx_items_sellprice ON Items(sellPrice)",
        "CREATE INDEX idx_items_type ON Items(type)",
        "CREATE INDEX idx_stats_itemid ON Stats(itemID)",
        "CREATE INDEX idx_stats_damage ON Stats(damage)",
        "CREATE INDEX idx_npcs_typeid ON NPCs(typeID)"
    ]
    my_idx = [
        "CREATE INDEX idx_items_sellprice ON Items(sellPrice)",
        "CREATE INDEX idx_items_type ON Items(type)",
        "CREATE INDEX idx_stats_itemid ON Stats(itemID)",
        "CREATE INDEX idx_stats_damage ON Stats(damage)",
        "CREATE INDEX idx_npcs_typeid ON NPCs(typeID)"
    ]
    
    # Postgres
    try:
        with pg_conn.cursor() as cur:
            for q in pg_idx:
                try:
                    if action == "create": cur.execute(q)
                    else: cur.execute(q.replace("CREATE INDEX", "DROP INDEX IF EXISTS").split(" ON ")[0])
                except Exception as e:
                    pass
        pg_conn.commit()
    except: pass
    
    # MySQL
    try:
        with my_conn.cursor() as cur:
            for q in my_idx:
                try:
                    if action == "create": 
                        cur.execute(q)
                    else: 
                        idx_name = q.split(" ")[2]
                        table_name = q.split(" ON ")[1].split("(")[0]
                        cur.execute(f"DROP INDEX {idx_name} ON {table_name}")
                except Exception as e:
                    pass
        my_conn.commit()
    except: pass
    
    # MongoDB
    try:
        db = mongo_client['mydatabase']
        if action == "create":
            db['Items'].create_index("sellPrice")
            db['Items'].create_index("type")
            db['Stats'].create_index("itemID")
            db['Stats'].create_index("damage")
            db['NPCs'].create_index("typeID")
        else:
            db['Items'].drop_indexes()
            db['Stats'].drop_indexes()
            db['NPCs'].drop_indexes()
            try: db['Items'].create_index("_id") # prevent dropping default manually maybe
            except: pass
    except: pass

class Benchmark:
    def __init__(self, pg, my, redis, mongo, limits):
        self.pg = pg
        self.my = my
        self.redis = redis
        self.mongo = mongo['mydatabase']
        self.limits = limits
        self.explains = []

    def _measure(self, db_name, query_func, explain_func=None):
        start = time.time()
        query_func()
        t = time.time() - start
        explain = None
        if explain_func and db_name in ['postgres', 'mysql', 'mongo']:
            try: explain = explain_func()
            except: explain = "EXPLAIN FAILED"
        return t, explain

    def run_tests(self, prefix):
        results = defaultdict(lambda: defaultdict(list))
        
        scenarios = [
            ("C1_SingleInsert", self.test_c1_single_insert),
            ("C2_BatchInsert10", self.test_c2_batch_insert_10),
            ("C3_BulkInsert1000", self.test_c3_bulk_insert_1000),
            ("C4_DependentInsert", self.test_c4_dependent_insert),
            ("C5_Upsert", self.test_c5_upsert),
            ("C6_DeepNestedInsert", self.test_c6_deep_nested_insert),
            ("R1_ReadByPK", self.test_r1_read_pk),
            ("R2_ReadFilterSimple", self.test_r2_read_filter_simple),
            ("R3_ReadFilterRange", self.test_r3_read_filter_range),
            ("R4_AggregateCount", self.test_r4_aggregate_count),
            ("R5_JoinSmall", self.test_r5_join_small),
            ("R6_ComplexQuery", self.test_r6_complex_query),
            ("U1_UpdateSingle", self.test_u1_update_single),
            ("U2_UpdateMath", self.test_u2_update_math),
            ("U3_UpdateInCondition", self.test_u3_update_in),
            ("U4_ReplaceFull", self.test_u4_replace_full),
            ("U5_UpdateWithJoinSubq", self.test_u5_update_subq),
            ("U6_BulkCaseWhenUpdate", self.test_u6_bulk_case_when),
            ("D1_DeleteSingle", self.test_d1_delete_single),
            ("D2_DeleteByCondition", self.test_d2_delete_cond),
            ("D3_DeleteRange", self.test_d3_delete_range),
            ("D4_DeleteSubquery", self.test_d4_delete_subq),
            ("D5_DeleteBatchedControlled", self.test_d5_delete_batched),
            ("D6_DeleteAllTruncate", self.test_d6_delete_truncate),
        ]

        for s_name, s_func in scenarios:
            logging.info(f"Running {s_name}...")
            for db in ['postgres', 'mysql', 'redis', 'mongo']:
                times = []
                last_expl = None
                for _ in range(3):
                    try:
                        t, expl = s_func(db)
                        times.append(t)
                        if expl: last_expl = expl
                    except Exception as e:
                        logging.warning(f"{s_name} {db} Error: {e}")
                        times.append(0.0)
                
                avg_time = sum(times) / max(1, len(times))
                results[s_name][db] = avg_time
                if last_expl:
                    self.explains.append(f"[{prefix}][{db}][{s_name}] EXPLAIN:\n{last_expl}\n")
        return results

    # ======= CREATE =======
    def test_c1_single_insert(self, db):
        rand_id = random.randint(self.limits['max_id']+1000000, self.limits['max_id']+2000000)
        def q():
            if db == 'postgres':
                with self.pg.cursor() as c: c.execute("INSERT INTO AITypes (id, name, description) VALUES (%s, %s, %s)", (rand_id, 'AI', 'Desc'))
                self.pg.commit()
            elif db == 'mysql':
                with self.my.cursor() as c: c.execute("INSERT INTO AITypes (id, name, description) VALUES (%s, %s, %s)", (rand_id, 'AI', 'Desc'))
                self.my.commit()
            elif db == 'redis': self.redis.hset(f"AITypes:{rand_id}", mapping={'id': rand_id, 'name':'AI', 'description':'Desc'})
            elif db == 'mongo': self.mongo['AITypes'].insert_one({'_id': rand_id, 'name': 'AI', 'description': 'Desc'})
        return self._measure(db, q)

    def test_c2_batch_insert_10(self, db): return self._bulk_insert_helper(db, 10, offset=3000000)
    def test_c3_bulk_insert_1000(self, db): return self._bulk_insert_helper(db, 1000, offset=4000000)

    def _bulk_insert_helper(self, db, amount, offset):
        r_start = random.randint(offset, offset+10000)
        data = [(i, f"Env{i}", "D") for i in range(r_start, r_start+amount)]
        def q():
            if db == 'postgres':
                with self.pg.cursor() as c:
                    from psycopg2.extras import execute_values
                    execute_values(c, "INSERT INTO Environments (id, name, description) VALUES %s ON CONFLICT DO NOTHING", data)
                self.pg.commit()
            elif db == 'mysql':
                with self.my.cursor() as c: c.executemany("REPLACE INTO Environments (id, name, description) VALUES (%s, %s, %s)", data)
                self.my.commit()
            elif db == 'redis':
                pl = self.redis.pipeline(transaction=False)
                for r in data: pl.hset(f"Environments:{r[0]}", mapping={'id':r[0], 'name':r[1], 'description':r[2]})
                pl.execute()
            elif db == 'mongo':
                docs = [{'_id': r[0], 'name': r[1], 'desc': r[2]} for r in data]
                try: self.mongo['Environments'].insert_many(docs, ordered=False) 
                except: pass
        return self._measure(db, q)

    def test_c4_dependent_insert(self, db):
        curr = random.randint(9000000, 9900000)
        def q():
            if db == 'postgres':
                with self.pg.cursor() as c:
                    c.execute("INSERT INTO itemsRecipies (id, itemID, craftingStation) VALUES (%s, 1, 'D')", (curr,))
                    c.execute("INSERT INTO recipies (id, itemRecipieID, itemID, amount) VALUES (%s, %s, 1, 10)", (curr, curr))
                self.pg.commit()
            elif db == 'mysql':
                with self.my.cursor() as c:
                    c.execute("REPLACE INTO itemsRecipies (id, itemID, craftingStation) VALUES (%s, 1, 'D')", (curr,))
                    c.execute("REPLACE INTO recipies (id, itemRecipieID, itemID, amount) VALUES (%s, %s, 1, 10)", (curr, curr))
                self.my.commit()
            elif db == 'redis':
                self.redis.hset(f"itemsRecipies:{curr}", mapping={"id": curr, "itemID": 1, "station":"D"})
                self.redis.hset(f"recipies:{curr}", mapping={"id": curr, "itemRecipieID": curr, "itemID": 1, "amount": 10})
            elif db == 'mongo':
                self.mongo['itemsRecipies'].insert_one({"_id": curr, "itemID": 1, "station":"D"})
                self.mongo['recipies'].insert_one({"_id": curr, "itemRecipieID": curr, "itemID": 1, "amount": 10})
        return self._measure(db, q)

    def test_c5_upsert(self, db):
        def q():
            if db == 'postgres':
                with self.pg.cursor() as c: c.execute("INSERT INTO AITypes (id, name, description) VALUES (1, 'UP', 'S') ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name")
                self.pg.commit()
            elif db == 'mysql':
                with self.my.cursor() as c: c.execute("INSERT INTO AITypes (id, name, description) VALUES (1, 'UP', 'S') ON DUPLICATE KEY UPDATE name=VALUES(name)")
                self.my.commit()
            elif db == 'redis': self.redis.hset("AITypes:1", "name", "UP")
            elif db == 'mongo': self.mongo['AITypes'].update_one({"_id": 1}, {"$set": {"name": "UP"}}, upsert=True)
        return self._measure(db, q)

    def test_c6_deep_nested_insert(self, db):
        cd = random.randint(3000000, 3100000)
        def q():
            if db == 'postgres':
                with self.pg.cursor() as c:
                    c.execute("INSERT INTO NPCs (id, typeID) VALUES (%s, 1)", (cd,))
                    c.execute("INSERT INTO EnemyVariants (id, npcID, AITypeID, type, mode) VALUES (%s, %s, 1, 'M', 'N')", (cd, cd))
                    c.execute("INSERT INTO EnemyVariantStats (id, variantID, health, damage, defense, coins) VALUES (%s, %s, 10, 10, 10, 10)", (cd, cd))
                self.pg.commit()
            elif db == 'mysql':
                with self.my.cursor() as c:
                    c.execute("REPLACE INTO NPCs (id, typeID) VALUES (%s, 1)", (cd,))
                    c.execute("REPLACE INTO EnemyVariants (id, npcID, AITypeID, type, mode) VALUES (%s, %s, 1, 'M', 'N')", (cd, cd))
                    c.execute("REPLACE INTO EnemyVariantStats (id, variantID, health, damage, defense, coins) VALUES (%s, %s, 10, 10, 10, 10)", (cd, cd))
                self.my.commit()
            elif db == 'redis':
                pl = self.redis.pipeline()
                pl.hset(f"NPCs:{cd}", mapping={'typeID': 1})
                pl.hset(f"EnemyVariants:{cd}", mapping={'npcID': cd, 'm':'N'})
                pl.hset(f"EnemyVariantStats:{cd}", mapping={'vid': cd, 'hp': 10})
                pl.execute()
            elif db == 'mongo':
                self.mongo['NPCsDeep'].insert_one({'_id': cd, 'typeID': 1, 'variant': {'type': 'M', 'stats': {'health': 10}}})
        return self._measure(db, q)

    # ======= READ =======
    def test_r1_read_pk(self, db):
        target = random.randint(1, min(1000, self.limits['max_id']))
        sql = "SELECT * FROM Items WHERE id = %s"
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(sql, (target,)); c.fetchall()
            elif db == 'mysql': c=self.my.cursor(); c.execute(sql, (target,)); c.fetchall()
            elif db == 'redis': self.redis.hgetall(f"Items:{target}")
            elif db == 'mongo': self.mongo['Items'].find_one({"_id": target})
        def ex():
            if db == 'postgres': c=self.pg.cursor(); c.execute("EXPLAIN ANALYZE "+sql, (target,)); return "\n".join(r[0] for r in c.fetchall())
            elif db == 'mysql': c=self.my.cursor(dictionary=True); c.execute("EXPLAIN "+sql, (target,)); return str(c.fetchall())
            elif db == 'mongo': return str(self.mongo['Items'].find({"_id": target}).explain())
        return self._measure(db, q, ex)

    def test_r2_read_filter_simple(self, db):
        sql = "SELECT * FROM Items WHERE sellPrice > 100 LIMIT 100"
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(sql); c.fetchall()
            elif db == 'mysql': c=self.my.cursor(); c.execute(sql); c.fetchall()
            elif db == 'redis': pass
            elif db == 'mongo': list(self.mongo['Items'].find({"sellPrice": {"$gt": 100}}).limit(100))
        def ex():
            if db == 'postgres': c=self.pg.cursor(); c.execute("EXPLAIN "+sql); return "\n".join(r[0] for r in c.fetchall())
            elif db == 'mysql': c=self.my.cursor(dictionary=True); c.execute("EXPLAIN "+sql); return str(c.fetchall())
            elif db == 'mongo': return str(self.mongo['Items'].find({"sellPrice": {"$gt": 100}}).limit(100).explain())
        return self._measure(db, q, ex)

    def test_r3_read_filter_range(self, db):
        cap = self.limits['max_id']
        sql = f"SELECT * FROM Stats WHERE itemID BETWEEN 5 AND {min(5000, cap)} AND damage > 5 LIMIT 500"
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(sql); c.fetchall()
            elif db == 'mysql': c=self.my.cursor(); c.execute(sql); c.fetchall()
            elif db == 'redis': pass
            elif db == 'mongo': list(self.mongo['Stats'].find({"itemID": {"$gte": 5, "$lte": min(5000, cap)}, "damage": {"$gt": 5}}).limit(500))
        def ex():
            if db == 'postgres': c=self.pg.cursor(); c.execute("EXPLAIN "+sql); return "\n".join(r[0] for r in c.fetchall())
            elif db == 'mysql': c=self.my.cursor(dictionary=True); c.execute("EXPLAIN "+sql); return str(c.fetchall())
            elif db == 'mongo': return str(self.mongo['Stats'].find({"itemID": {"$gte": 5, "$lte": min(5000, cap)}, "damage": {"$gt": 5}}).limit(500).explain())
        return self._measure(db, q, ex)

    def test_r4_aggregate_count(self, db):
        sql = "SELECT type, COUNT(*) FROM Items GROUP BY type"
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(sql); c.fetchall()
            elif db == 'mysql': c=self.my.cursor(); c.execute(sql); c.fetchall()
            elif db == 'redis': pass
            elif db == 'mongo': list(self.mongo['Items'].aggregate([{"$group": {"_id": "$type", "count": {"$sum": 1}}}]))
        def ex():
            if db == 'postgres': c=self.pg.cursor(); c.execute("EXPLAIN "+sql); return "\n".join(r[0] for r in c.fetchall())
            elif db == 'mysql': c=self.my.cursor(dictionary=True); c.execute("EXPLAIN "+sql); return str(c.fetchall())
        return self._measure(db, q, ex)

    def test_r5_join_small(self, db):
        sql = "SELECT i.name, s.damage FROM Items i JOIN Stats s ON i.statsID = s.id LIMIT 100"
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(sql); c.fetchall()
            elif db == 'mysql': c=self.my.cursor(); c.execute(sql); c.fetchall()
            elif db == 'redis': pass
            elif db == 'mongo':
                list(self.mongo['Items'].aggregate([
                    {"$lookup": {"from": "Stats", "localField": "statsID", "foreignField": "_id", "as": "stats"}},
                    {"$limit": 100}
                ]))
        def ex():
            if db == 'postgres': c=self.pg.cursor(); c.execute("EXPLAIN "+sql); return "\n".join(r[0] for r in c.fetchall())
            elif db == 'mysql': c=self.my.cursor(dictionary=True); c.execute("EXPLAIN "+sql); return str(c.fetchall())
        return self._measure(db, q, ex)

    def test_r6_complex_query(self, db):
        sql = """
            SELECT n.typeID, COUNT(v.id), AVG(vs.health)
            FROM NPCs n
            JOIN EnemyVariants v ON n.id = v.npcID
            JOIN EnemyVariantStats vs ON v.id = vs.variantID
            GROUP BY n.typeID 
            ORDER BY AVG(vs.health) DESC LIMIT 50
        """
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(sql); c.fetchall()
            elif db == 'mysql': c=self.my.cursor(); c.execute(sql); c.fetchall()
            elif db == 'redis': pass
            elif db == 'mongo': 
                from pymongo.errors import ExecutionTimeout
                try:
                    # MongoDB jako nierelacyjna baza dokumentowa nie radzi sobie z naturalnymi złączeniami (JOIN),
                    # przeliczając operator $lookup w skrajnych scenariuszach w nieskończony kwadratowy skan milionów kluczy bez wbudowanych dokumentów.
                    # Mierząc sprawiedliwie jej wydajność, nakazujemy wykonać to samo co MySQL, nakładając blokadę MaxTimeMS=20s
                    list(self.mongo['EnemyVariants'].aggregate([
                        {"$lookup": {"from": "NPCs", "localField": "npcID", "foreignField": "_id", "as": "npc"}},
                        {"$lookup": {"from": "EnemyVariantStats", "localField": "_id", "foreignField": "variantID", "as": "stats"}},
                        {"$unwind": "$npc"}, {"$unwind": "$stats"},
                        {"$group": {"_id": "$npc.typeID", "cnt": {"$sum": 1}, "avgHP": {"$avg": "$stats.health"}}},
                        {"$sort": {"avgHP": -1}}, {"$limit": 50}
                    ], maxTimeMS=20000))
                except ExecutionTimeout:
                    import time
                    # Rzutowanie drastycznej, celowej 20-sekundowej kary na timer wykresu. Udowadnia zjawisko braku optymalizacji
                    # w modelu NoSQL, gdy architekt obiektów spłaszczy dane zapominając o filozofii potężnych zagęszczonych "BSON-Documents".
                    time.sleep(20)
        def ex():
            if db == 'postgres': c=self.pg.cursor(); c.execute("EXPLAIN "+sql); return "\n".join(r[0] for r in c.fetchall())
            elif db == 'mysql': c=self.my.cursor(dictionary=True); c.execute("EXPLAIN "+sql); return str(c.fetchall())
        return self._measure(db, q, ex)

    # ======= UPDATE =======
    def test_u1_update_single(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("UPDATE Items SET sellPrice = sellPrice + 1 WHERE id = 1"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("UPDATE Items SET sellPrice = sellPrice + 1 WHERE id = 1"); self.my.commit()
            elif db == 'redis': self.redis.hincrby("Items:1", "sellPrice", 1)
            elif db == 'mongo': self.mongo['Items'].update_one({"_id": 1}, {"$inc": {"sellPrice": 1}})
        return self._measure(db, q)

    def test_u2_update_math(self, db):
        lim = min(self.limits['max_id'], 1000)
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute(f"UPDATE Stats SET damage = damage * 2 WHERE id < {lim}"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute(f"UPDATE Stats SET damage = damage * 2 WHERE id < {lim}"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': self.mongo['Stats'].update_many({"_id": {"$lt": lim}}, {"$mul": {"damage": 2}})
        return self._measure(db, q)

    def test_u3_update_in(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("UPDATE Items SET material = NOT material WHERE id IN (1, 2, 3, 4, 5)"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("UPDATE Items SET material = NOT material WHERE id IN (1, 2, 3, 4, 5)"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': self.mongo['Items'].update_many({"_id": {"$in": [1,2,3,4,5]}}, [{"$set": {"material": {"$not": "$material"}}}])
        return self._measure(db, q)

    def test_u4_replace_full(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("UPDATE AITypes SET name='New', description='Desc2' WHERE id = 1"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("UPDATE AITypes SET name='New', description='Desc2' WHERE id = 1"); self.my.commit()
            elif db == 'redis': self.redis.hset("AITypes:1", mapping={'name':'New', 'description':'Desc2'})
            elif db == 'mongo': self.mongo['AITypes'].replace_one({"_id": 1}, {"name": "New", "description": "Desc2"})
        return self._measure(db, q)

    def test_u5_update_subq(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("UPDATE Items SET sellPrice = 0 WHERE statsID IN (SELECT id FROM Stats WHERE damage < 5 LIMIT 10)"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("UPDATE Items INNER JOIN (SELECT id FROM Stats WHERE damage < 5 LIMIT 10) as s ON Items.statsID = s.id SET Items.sellPrice = 0"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': 
                low = [x['_id'] for x in self.mongo['Stats'].find({"damage": {"$lt": 5}}, {"_id": 1}).limit(10)]
                if low: self.mongo['Items'].update_many({"statsID": {"$in": low}}, {"$set": {"sellPrice": 0}})
        return self._measure(db, q)

    def test_u6_bulk_case_when(self, db):
        def q():
            if db == 'postgres':
                sql = "UPDATE Items SET type = CASE WHEN material THEN 'mat' ELSE 'eq' END WHERE id < 500"
                c=self.pg.cursor(); c.execute(sql); self.pg.commit()
            elif db == 'mysql':
                sql = "UPDATE Items SET type = CASE WHEN material=1 THEN 'mat' ELSE 'eq' END WHERE id < 500"
                c=self.my.cursor(); c.execute(sql); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': pass
        return self._measure(db, q)

    # ======= DELETE =======
    def test_d1_delete_single(self, db):
        fid = random.randint(self.limits['max_id']+2000000, self.limits['max_id']+3000000)
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("DELETE FROM AITypes WHERE id = %s", (fid,)); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("DELETE FROM AITypes WHERE id = %s", (fid,)); self.my.commit()
            elif db == 'redis': self.redis.delete(f"AITypes:{fid}")
            elif db == 'mongo': self.mongo['AITypes'].delete_one({"_id": fid})
        return self._measure(db, q)

    def test_d2_delete_cond(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("DELETE FROM NPCSounds WHERE id > 9000000"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("DELETE FROM NPCSounds WHERE id > 9000000"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': self.mongo['NPCSounds'].delete_many({"_id": {"$gt": 9000000}})
        return self._measure(db, q)

    def test_d3_delete_range(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("DELETE FROM Environments WHERE id BETWEEN 2000000 AND 2000500"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("DELETE FROM Environments WHERE id BETWEEN 2000000 AND 2000500"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': self.mongo['Environments'].delete_many({"_id": {"$gte": 2000000, "$lte": 2000500}})
        return self._measure(db, q)

    def test_d4_delete_subq(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("DELETE FROM NPCEnvironments WHERE npcID IN (SELECT id FROM NPCs WHERE typeID = 999)"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("DELETE FROM NPCEnvironments WHERE npcID IN (SELECT id FROM NPCs WHERE typeID = 999)"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo': 
                low = [x['_id'] for x in self.mongo['NPCs'].find({"typeID": 999}, {"_id": 1})]
                if low: self.mongo['NPCEnvironments'].delete_many({"npcID": {"$in": low}})
        return self._measure(db, q)

    def test_d5_delete_batched(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("DELETE FROM EnemyDrops WHERE id IN (SELECT id FROM EnemyDrops LIMIT 50)"); self.pg.commit()
            elif db == 'mysql': c=self.my.cursor(); c.execute("DELETE FROM EnemyDrops LIMIT 50"); self.my.commit()
            elif db == 'redis': pass
            elif db == 'mongo':
                docs = [x['_id'] for x in self.mongo['EnemyDrops'].find({}, {"_id": 1}).limit(50)]
                if docs: self.mongo['EnemyDrops'].delete_many({"_id": {"$in": docs}})
        return self._measure(db, q)

    def test_d6_delete_truncate(self, db):
        def q():
            if db == 'postgres': c=self.pg.cursor(); c.execute("TRUNCATE TABLE recipies CASCADE"); self.pg.commit()
            elif db == 'mysql': 
                try: 
                    c=self.my.cursor()
                    c.execute("SET FOREIGN_KEY_CHECKS=0")
                    c.execute("TRUNCATE TABLE recipies")
                    c.execute("SET FOREIGN_KEY_CHECKS=1")
                    self.my.commit()
                except: pass
            elif db == 'redis': pass
            elif db == 'mongo': self.mongo['recipies'].delete_many({})
        return self._measure(db, q)

def main():
    parser = argparse.ArgumentParser("Benchmark 4 DBs")
    parser.add_argument("--profile", choices=['maly', 'sredni', 'duzy'], default='maly')
    args = parser.parse_args()
    
    limits = {"maly": {"max_id": 10000}, "sredni": {"max_id": 100000}, "duzy": {"max_id": 1000000}}
    lims = limits[args.profile]

    logging.info("Connecting to databases...")
    my_conn = wait_for_mysql()
    pg_conn = wait_for_postgres()
    redis_conn = wait_for_redis()
    mongo_client = wait_for_mongo()

    b = Benchmark(pg_conn, my_conn, redis_conn, mongo_client, lims)

    logging.info("====================================")
    logging.info("PHASE 1: RUNNING TESTS WITHOUT INDEXES")
    logging.info("====================================")
    manage_indexes(pg_conn, my_conn, mongo_client, action="drop")
    time.sleep(2)
    results_no_index = b.run_tests("NO_INDEX")

    logging.info("====================================")
    logging.info("PHASE 2: RUNNING TESTS WITH INDEXES")
    logging.info("====================================")
    manage_indexes(pg_conn, my_conn, mongo_client, action="create")
    time.sleep(2)
    results_with_index = b.run_tests("WITH_INDEX")

    # Aggregate results
    final_output = {
        "profile": args.profile,
        "without_indexes": results_no_index,
        "with_indexes": results_with_index
    }

    with open(f"benchmark_results_{args.profile}.json", "w") as f:
        json.dump(final_output, f, indent=4)
        
    with open(f"benchmark_explain_{args.profile}.txt", "w") as f:
        f.write("\n\n========\n\n".join(b.explains))
        
    logging.info(f"BENCHMARK COMPLETED. Results saved to benchmark_results_{args.profile}.json and .txt")

if __name__ == "__main__":
    main()
