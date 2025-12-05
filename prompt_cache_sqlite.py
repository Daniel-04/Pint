import sqlite3
import hashlib
import json
import os

class PromptCache:
    # Handles local caching of prompts using SQLite.

    def __init__(self, cache_folder="cache", cache_file="api_cache.db"):
        os.makedirs(cache_folder, exist_ok=True)
        db_path = os.path.join(cache_folder,cache_file)
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id TEXT PRIMARY KEY,
                    model_engine TEXT,
                    response TEXT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _generate_hash(self, model_engine, system, prompt):

        hashkey = ".".join(["prompt-caching-v1", str(model_engine), system, prompt])
        return hashlib.md5(hashkey.encode()).hexdigest()

    def get_cached_response(self, model_engine, system, prompt):
        hash_value = self._generate_hash(model_engine, system, prompt)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT response FROM cache WHERE id = ?", (hash_value,))
            result = cursor.fetchone()

            if result:
                return json.loads(result[0])  # Convert string back to JSON
            return None  # No cached response found


    def purge_old_data(self, cutoff_date, model_engine = None):
        #Removes old rows, optionally a specific model 
 
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()            
            if model_engine:
                cursor.execute("DELETE FROM cache WHERE date < ? and model_engine LIKE ", (cutoff_date,model_engine))
            else:
                cursor.execute("DELETE FROM cache WHERE date < ?", (cutoff_date,))
            conn.commit()

  

    def save_response(self, model_engine, system, prompt, response):
         
        hash_value = self._generate_hash(model_engine, system, prompt)
        response_json = json.dumps(response)  # Convert to JSON string

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cache (id, model_engine, response)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET response=excluded.response
            """, (hash_value, model_engine, response_json))
            conn.commit()
