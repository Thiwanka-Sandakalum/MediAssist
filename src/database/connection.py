"""Database connection management for MediAssist.

Provides connection pooling and lifecycle management for PostgreSQL connections.
Week 2 MVP: Simple pooling. Week 3+: Add migrations, advanced pooling.
"""

import logging
import psycopg2
from psycopg2 import pool
from typing import Optional

from src.config import config

logger = logging.getLogger(__name__)

# Global connection pool (initialized at startup)
_pool: Optional[pool.SimpleConnectionPool] = None


def init_connection_pool() -> None:
	"""Initialize the database connection pool.
	
	Called during app startup. Creates a connection pool with configured
	min/max connections.
	"""
	global _pool
	try:
		_pool = pool.SimpleConnectionPool(
			minconn=2,
			maxconn=20,
			dsn=config.DATABASE_URL
		)
		logger.info(f"Connection pool initialized: {config.DATABASE_URL}")
	except Exception as e:
		logger.error(f"Failed to initialize connection pool: {str(e)}")
		raise


def get_db_connection():
	"""Get a connection from the pool.
	
	Returns:
		psycopg2 connection object
		
	Raises:
		RuntimeError: If pool not initialized
	"""
	if _pool is None:
		raise RuntimeError("Connection pool not initialized. Call init_connection_pool() first.")
	try:
		conn = _pool.getconn()
		conn.autocommit = True  # Auto-commit for simplicity (Week 3: transaction management)
		return conn
	except Exception as e:
		logger.error(f"Failed to get connection from pool: {str(e)}")
		raise


def return_db_connection(conn) -> None:
	"""Return a connection to the pool.
	
	Args:
		conn: psycopg2 connection object to return
	"""
	if _pool is not None and conn is not None:
		try:
			_pool.putconn(conn)
		except Exception as e:
			logger.error(f"Failed to return connection to pool: {str(e)}")
			# Force close if put fails
			try:
				conn.close()
			except:
				pass


def close_all_connections() -> None:
	"""Close all connections in the pool.
	
	Called during app shutdown. Gracefully closes all pooled connections.
	"""
	global _pool
	if _pool is not None:
		try:
			_pool.closeall()
			logger.info("Connection pool closed")
			_pool = None
		except Exception as e:
			logger.error(f"Error closing connection pool: {str(e)}")


def execute_query(query: str, params: tuple = None) -> list:
	"""Execute a SELECT query and return results.
	
	Simple utility for one-off queries. For complex operations,
	get connection and manage manually.
	
	Args:
		query: SQL query string
		params: Query parameters tuple
		
	Returns:
		List of result rows as dicts
	"""
	conn = get_db_connection()
	try:
		cursor = conn.cursor()
		cursor.execute(query, params or ())
		columns = [desc[0] for desc in cursor.description] if cursor.description else []
		results = [dict(zip(columns, row)) for row in cursor.fetchall()]
		cursor.close()
		return results
	except Exception as e:
		logger.error(f"Query execution failed: {str(e)}")
		raise
	finally:
		return_db_connection(conn)
