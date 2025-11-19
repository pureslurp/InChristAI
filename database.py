"""
Database abstraction layer for PostgreSQL (Railway)
Requires DATABASE_URL environment variable to be set.
"""
import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for PostgreSQL (Railway)"""
    
    def __init__(self, database_url: Optional[str] = None):
        # Require DATABASE_URL to be set - no SQLite fallback
        self.database_url = database_url or os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Please set it to your PostgreSQL connection string. "
                "Example: postgresql://user:password@host:port/database"
            )
        
        self.is_postgres = self.database_url.startswith('postgresql://') or self.database_url.startswith('postgres://')
        
        if not self.is_postgres:
            raise ValueError(
                f"Only PostgreSQL databases are supported. "
                f"DATABASE_URL must start with 'postgresql://' or 'postgres://'. "
                f"Current value: {self.database_url[:50]}..."
            )
        
        self._init_postgres()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            import psycopg2
            
            # Parse DATABASE_URL for PostgreSQL
            if self.database_url.startswith('postgresql://'):
                url = self.database_url[13:]
            else:
                url = self.database_url[11:]
            
            # Parse the URL components
            if '@' in url:
                user_pass, host_db = url.split('@', 1)
                if ':' in user_pass:
                    username, password = user_pass.split(':', 1)
                else:
                    username, password = user_pass, ''
                
                if '/' in host_db:
                    host_port, database = host_db.split('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                    else:
                        host, port = host_port, '5432'
                else:
                    host, port, database = host_port, '5432', 'postgres'
            else:
                # Fallback parsing
                username = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', '')
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                database = os.getenv('DB_NAME', 'inchrist_ai')
            
            self.connection_params = {
                'host': host,
                'port': port,
                'database': database,
                'user': username,
                'password': password
            }
            
            logger.info(f"PostgreSQL connection configured for {host}:{port}/{database}")
            
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
    
    def _init_sqlite(self):
        """Initialize SQLite connection"""
        # Extract file path from sqlite URL
        if self.database_url.startswith('sqlite:///'):
            self.db_path = self.database_url[10:]  # Remove 'sqlite:///'
        else:
            self.db_path = 'inchrist_ai.db'
        
        logger.info(f"SQLite database path: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        if self.is_postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = None
            try:
                conn = psycopg2.connect(**self.connection_params)
                conn.autocommit = False
                yield conn
                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"PostgreSQL connection error: {e}")
                raise
            finally:
                if conn:
                    conn.close()
        else:
            import sqlite3
            
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                yield conn
                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"SQLite connection error: {e}")
                raise
            finally:
                if conn:
                    conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.is_postgres:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(query, params or ())
            
            if self.is_postgres:
                return [dict(row) for row in cursor.fetchall()]
            else:
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = None) -> Any:
        """Execute INSERT query and return the inserted ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if self.is_postgres:
                return cursor.fetchone()[0] if cursor.description else None
            else:
                return cursor.lastrowid
    
    def init_tables(self):
        """Initialize database tables"""
        logger.info("Initializing database tables...")
        
        # Table for tracking mentions and responses
        interactions_table = """
        CREATE TABLE IF NOT EXISTS interactions (
            id SERIAL PRIMARY KEY,
            tweet_id TEXT UNIQUE,
            user_id TEXT,
            username TEXT,
            mention_text TEXT,
            response_text TEXT,
            response_tweet_id TEXT,
            created_at TIMESTAMP,
            responded_at TIMESTAMP,
            interaction_type TEXT,
            status TEXT DEFAULT 'pending'
        )
        """ if self.is_postgres else """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT UNIQUE,
            user_id TEXT,
            username TEXT,
            mention_text TEXT,
            response_text TEXT,
            response_tweet_id TEXT,
            created_at TIMESTAMP,
            responded_at TIMESTAMP,
            interaction_type TEXT,
            status TEXT DEFAULT 'pending'
        )
        """
        
        # Table for tracking daily posts
        daily_posts_table = """
        CREATE TABLE IF NOT EXISTS daily_posts (
            id SERIAL PRIMARY KEY,
            date DATE UNIQUE,
            verse_reference TEXT,
            verse_text TEXT,
            tweet_id TEXT,
            reply_tweet_id TEXT,
            posted_at TIMESTAMP
        )
        """ if self.is_postgres else """
        CREATE TABLE IF NOT EXISTS daily_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE,
            verse_reference TEXT,
            verse_text TEXT,
            tweet_id TEXT,
            reply_tweet_id TEXT,
            posted_at TIMESTAMP
        )
        """
        
        # Table for user preferences and history
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            last_interaction TIMESTAMP,
            interaction_count INTEGER DEFAULT 0,
            preferred_version TEXT DEFAULT 'ESV',
            is_blocked BOOLEAN DEFAULT FALSE
        )
        """
        
        # Create tables
        self.execute_update(interactions_table)
        self.execute_update(daily_posts_table)
        self.execute_update(users_table)
        
        # Create indexes for better performance
        if self.is_postgres:
            self.execute_update("CREATE INDEX IF NOT EXISTS idx_interactions_tweet_id ON interactions(tweet_id)")
            self.execute_update("CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id)")
            self.execute_update("CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at)")
            self.execute_update("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
        
        logger.info("Database tables initialized successfully")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Total interactions
            total_interactions = self.execute_query("SELECT COUNT(*) as count FROM interactions")[0]['count']
            
            # Successful responses
            successful_responses = self.execute_query(
                "SELECT COUNT(*) as count FROM interactions WHERE status = 'completed'"
            )[0]['count']
            
            # Today's activity
            if self.is_postgres:
                today_activity = self.execute_query(
                    "SELECT COUNT(*) as count FROM interactions WHERE DATE(created_at) = CURRENT_DATE"
                )[0]['count']
            else:
                today_activity = self.execute_query(
                    "SELECT COUNT(*) as count FROM interactions WHERE DATE(created_at) = DATE('now')"
                )[0]['count']
            
            # Unique users
            unique_users = self.execute_query("SELECT COUNT(DISTINCT user_id) as count FROM interactions")[0]['count']
            
            return {
                'total_interactions': total_interactions,
                'successful_responses': successful_responses,
                'today_interactions': today_activity,
                'unique_users': unique_users,
                'response_rate': (successful_responses / total_interactions * 100) if total_interactions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up old interaction data
        
        Only deletes old PENDING interactions (never responded to).
        Keeps all completed/failed interactions to prevent duplicate responses.
        """
        try:
            if self.is_postgres:
                # Only delete old pending interactions (never responded to)
                # Keep all completed/failed interactions to prevent duplicate responses
                deleted_count = self.execute_update(
                    "DELETE FROM interactions WHERE created_at < NOW() - INTERVAL '%s days' AND status = 'pending'" % days
                )
            else:
                deleted_count = self.execute_update(
                    "DELETE FROM interactions WHERE created_at < datetime('now', '-%d days') AND status = 'pending'" % days
                )
            logger.info(f"Cleaned up {deleted_count} old pending interactions (kept all completed/failed interactions)")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
