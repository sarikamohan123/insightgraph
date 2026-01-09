"""
Infrastructure Tests
====================

Tests for verifying external dependencies:
- Redis connectivity
- PostgreSQL connectivity
- Docker container health

These tests verify that the infrastructure is properly set up
before running application tests.
"""

import pytest
import redis
import psycopg2
from config import settings


class TestRedisInfrastructure:
    """Test Redis connectivity and basic operations"""

    def test_redis_connection(self):
        """Verify Redis is accessible and responding"""
        # Connect to Redis
        client = redis.from_url(settings.redis_url)

        # Test basic ping
        assert client.ping() is True, "Redis should respond to PING"

        client.close()

    def test_redis_set_get(self):
        """Verify Redis can store and retrieve data"""
        client = redis.from_url(settings.redis_url)

        # Set a test key
        test_key = "test:infrastructure"
        test_value = "hello_redis"
        client.set(test_key, test_value, ex=60)  # Expire in 60 seconds

        # Retrieve and verify
        retrieved = client.get(test_key)
        assert retrieved.decode('utf-8') == test_value

        # Cleanup
        client.delete(test_key)
        client.close()

    def test_redis_expiration(self):
        """Verify Redis TTL functionality works"""
        client = redis.from_url(settings.redis_url)

        test_key = "test:ttl"
        client.set(test_key, "temporary", ex=10)  # 10 second TTL

        # Check TTL is set
        ttl = client.ttl(test_key)
        assert ttl > 0 and ttl <= 10, "TTL should be between 0 and 10 seconds"

        # Cleanup
        client.delete(test_key)
        client.close()


class TestPostgreSQLInfrastructure:
    """Test PostgreSQL connectivity and basic operations"""

    def test_postgres_connection(self):
        """Verify PostgreSQL is accessible"""
        # Parse database URL
        # Format: postgresql://user:password@host:port/database
        db_url = settings.database_url

        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        assert conn is not None, "Should connect to PostgreSQL"

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result[0] == 1, "Should execute basic query"

        cursor.close()
        conn.close()

    def test_postgres_database_exists(self):
        """Verify the insightgraph database exists"""
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()

        # Check database exists
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        assert db_name == "insightgraph", "Should be connected to insightgraph database"

        cursor.close()
        conn.close()

    def test_postgres_can_create_table(self):
        """Verify we can create and drop tables"""
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_infrastructure (
                id SERIAL PRIMARY KEY,
                test_data TEXT
            )
        """)
        conn.commit()

        # Verify table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'test_infrastructure'
            )
        """)
        exists = cursor.fetchone()[0]
        assert exists is True, "Table should exist after creation"

        # Cleanup - drop table
        cursor.execute("DROP TABLE IF EXISTS test_infrastructure")
        conn.commit()

        cursor.close()
        conn.close()


class TestDockerContainersHealth:
    """Test Docker containers are running and healthy"""

    def test_both_services_accessible(self):
        """Verify both Redis and PostgreSQL are accessible"""
        # Test Redis
        redis_client = redis.from_url(settings.redis_url)
        assert redis_client.ping() is True
        redis_client.close()

        # Test PostgreSQL
        pg_conn = psycopg2.connect(settings.database_url)
        cursor = pg_conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
        cursor.close()
        pg_conn.close()


# Pytest fixtures for reusable connections
@pytest.fixture
def redis_client():
    """Provide a Redis client for tests"""
    client = redis.from_url(settings.redis_url)
    yield client
    client.close()


@pytest.fixture
def postgres_connection():
    """Provide a PostgreSQL connection for tests"""
    conn = psycopg2.connect(settings.database_url)
    yield conn
    conn.close()
