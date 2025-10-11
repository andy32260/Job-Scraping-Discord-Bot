import sqlite3
import json
from typing import List, Dict

class DatabaseManager:
    def __init__(self, db_path: str = "job_bot.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        #bookmarks entity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                job_title TEXT NOT NULL,
                employer_name TEXT NOT NULL,
                job_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        #search history entity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_user_id ON search_history(user_id)')

        conn.commit()
        conn.close()

    def add_bookmark(self, user_id: int, job: Dict) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM bookmarks 
            WHERE user_id = ? AND job_title = ? AND employer_name = ?
        ''', (str(user_id), job.get('job_title', ''), job.get('employer_name', '')))

        if cursor.fetchone():
            conn.close()
            return False

        cursor.execute('''
            INSERT INTO bookmarks (user_id, job_title, employer_name, job_data)
            VALUES (?, ?, ?, ?)
        ''', (str(user_id), job.get('job_title', ''), job.get('employer_name', ''), json.dumps(job)))

        conn.commit()
        conn.close()
        return True

    def get_bookmarks(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT job_data FROM bookmarks 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (str(user_id),))

        bookmarks = []
        for row in cursor.fetchall():
            try:
                job_data = json.loads(row[0])
                bookmarks.append(job_data)
            except json.JSONDecodeError:
                continue

        conn.close()
        return bookmarks

    def clear_bookmarks(self, user_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM bookmarks WHERE user_id = ?', (str(user_id),))
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()
        return deleted_count

    def add_search_history(self, user_id: int, query: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO search_history (user_id, query)
            VALUES (?, ?)
        ''', (str(user_id), query))

        cursor.execute('''
            DELETE FROM search_history 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM search_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            )
        ''', (str(user_id), str(user_id)))

        conn.commit()
        conn.close()

    def get_search_history(self, user_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT query, timestamp FROM search_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (str(user_id),))

        history = []
        for row in cursor.fetchall():
            history.append({
                'query': row[0],
                'timestamp': row[1]
            })

        conn.close()
        return history

    def clear_search_history(self, user_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM search_history WHERE user_id = ?', (str(user_id),))
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()
        return deleted_count

    def clear_all_user_data(self, user_id: int) -> tuple:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM bookmarks WHERE user_id = ?', (str(user_id),))
        bookmarks_deleted = cursor.rowcount

        cursor.execute('DELETE FROM search_history WHERE user_id = ?', (str(user_id),))
        history_deleted = cursor.rowcount

        conn.commit()
        conn.close()
        return bookmarks_deleted, history_deleted


