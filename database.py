import os
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

load_dotenv()

class DatabaseProvider:
    def __init__(self):
        self.use_supabase = False
        self.supabase_client: Optional[Client] = None
        self.sqlite_path = "bot_database.db"
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if HAS_SUPABASE and supabase_url and supabase_key:
            try:
                self.supabase_client = create_client(supabase_url, supabase_key)
                self.use_supabase = True
                print("[DB] Usando Supabase (PostgreSQL) para persistencia.")
            except Exception as e:
                print(f"[DB] Error iniciando Supabase: {e}. Cayendo a SQLite.")
                self.use_supabase = False
        else:
            print("[DB] Credenciales de Supabase no encontradas o librería ausente. Usando SQLite.")
            
        if not self.use_supabase:
            self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        cur = conn.cursor()
        
        # Tabla documents
        cur.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            document_type TEXT,
            document_number TEXT,
            url TEXT UNIQUE,
            hash_content TEXT UNIQUE,
            title TEXT,
            extracted_text TEXT,
            published_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabla analysis
        cur.execute('''
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            publish_decision BOOLEAN,
            final_score INTEGER,
            discard_reason TEXT,
            main_topic TEXT,
            summary_internal TEXT,
            infographic_type TEXT,
            effective_date TEXT,
            confidence_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
        ''')
        
        # Tabla posts
        cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            text_content TEXT,
            infographic_layout_json TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(analysis_id) REFERENCES analysis(id)
        )
        ''')
        
        # Tabla publications
        cur.execute('''
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            platform TEXT,
            status TEXT,
            published_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
        ''')
        
        # Tabla logs
        cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def is_duplicate(self, url: str = None, hash_content: str = None, document_number: str = None) -> bool:
        """Verifica si un documento ya existe usando url, hash o número de doc"""
        if self.use_supabase:
            if url:
                res = self.supabase_client.table("documents").select("id").eq("url", url).execute()
                if res.data: return True
            if hash_content:
                res = self.supabase_client.table("documents").select("id").eq("hash_content", hash_content).execute()
                if res.data: return True
            if document_number:
                res = self.supabase_client.table("documents").select("id").eq("document_number", document_number).execute()
                if res.data: return True
            return False
            
        else:
            conn = sqlite3.connect(self.sqlite_path)
            cur = conn.cursor()
            
            if url:
                cur.execute("SELECT id FROM documents WHERE url = ?", (url,))
                if cur.fetchone(): return True
            if hash_content:
                cur.execute("SELECT id FROM documents WHERE hash_content = ?", (hash_content,))
                if cur.fetchone(): return True
            if document_number:
                cur.execute("SELECT id FROM documents WHERE document_number = ?", (document_number,))
                if cur.fetchone(): return True
            
            conn.close()
            return False

    def insert_document(self, data: Dict[str, Any]) -> Any:
        """Inserta un documento y devuelve su ID"""
        if self.use_supabase:
            # Eliminar nulls para supabase si no están en schema
            res = self.supabase_client.table("documents").insert(data).execute()
            if res.data:
                return res.data[0]['id']
            return None
        else:
            conn = sqlite3.connect(self.sqlite_path)
            cur = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            sql = f'INSERT INTO documents ({columns}) VALUES ({placeholders})'
            cur.execute(sql, list(data.values()))
            doc_id = cur.lastrowid
            conn.commit()
            conn.close()
            return doc_id

    def insert_analysis(self, data: Dict[str, Any]) -> Any:
        if self.use_supabase:
            res = self.supabase_client.table("analysis").insert(data).execute()
            if res.data:
                return res.data[0]['id']
            return None
        else:
            conn = sqlite3.connect(self.sqlite_path)
            cur = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            sql = f'INSERT INTO analysis ({columns}) VALUES ({placeholders})'
            cur.execute(sql, list(data.values()))
            aid = cur.lastrowid
            conn.commit()
            conn.close()
            return aid

    def insert_post(self, data: Dict[str, Any]) -> Any:
        if self.use_supabase:
            res = self.supabase_client.table("posts").insert(data).execute()
            if res.data:
                return res.data[0]['id']
            return None
        else:
            conn = sqlite3.connect(self.sqlite_path)
            cur = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            sql = f'INSERT INTO posts ({columns}) VALUES ({placeholders})'
            cur.execute(sql, list(data.values()))
            pid = cur.lastrowid
            conn.commit()
            conn.close()
            return pid
            
    def insert_publication(self, data: Dict[str, Any]) -> Any:
        if self.use_supabase:
            res = self.supabase_client.table("publications").insert(data).execute()
            if res.data:
                return res.data[0]['id']
            return None
        else:
            conn = sqlite3.connect(self.sqlite_path)
            cur = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            sql = f'INSERT INTO publications ({columns}) VALUES ({placeholders})'
            cur.execute(sql, list(data.values()))
            pid = cur.lastrowid
            conn.commit()
            conn.close()
            return pid

    def log_event(self, level: str, message: str, details: str = ""):
        data = {"level": level, "message": message, "details": details}
        if self.use_supabase:
            self.supabase_client.table("logs").insert(data).execute()
        else:
            conn = sqlite3.connect(self.sqlite_path)
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (level, message, details) VALUES (?, ?, ?)", 
                        (data["level"], data["message"], data["details"]))
            conn.commit()
            conn.close()

# Exportamos una instancia global opcionalmente o permitimos que main.py la inicialice
db = DatabaseProvider()
