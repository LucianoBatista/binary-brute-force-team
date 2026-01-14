"""Redis client service for session and chat storage."""

import json
from typing import Any, Optional, List
from redis import Redis
from redis.exceptions import RedisError
from project.config import get_settings


class RedisClient:
    """
    Singleton Redis client for managing chat sessions and messages.

    Provides helper methods for JSON serialization, TTL management,
    and common operations like lists and key-value storage.
    """

    _instance: Optional["RedisClient"] = None
    _client: Optional[Redis] = None

    # Default TTL: 24 hours (in seconds)
    DEFAULT_TTL = 86400

    def __new__(cls):
        """Ensure only one instance of RedisClient exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Redis connection if not already connected."""
        if self._client is None:
            settings = get_settings()
            # Parse broker_url (format: redis://host:port/db)
            broker_url = settings.broker_url
            self._client = Redis.from_url(
                broker_url,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )

    @property
    def client(self) -> Redis:
        """Get the Redis client instance."""
        if self._client is None:
            raise RedisError("Redis client not initialized")
        return self._client

    def ping(self) -> bool:
        """
        Check if Redis connection is alive.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            return self.client.ping()
        except RedisError:
            return False

    # JSON Operations

    def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store a JSON-serializable object in Redis.

        Args:
            key: Redis key
            value: Python object (dict, list, etc.)
            ttl: Time-to-live in seconds (default: 24 hours)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_str = json.dumps(value)
            if ttl is None:
                ttl = self.DEFAULT_TTL
            return self.client.setex(key, ttl, json_str)
        except (RedisError, TypeError, ValueError) as e:
            print(f"Error setting JSON key {key}: {e}")
            return False

    def get_json(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a JSON object from Redis.

        Args:
            key: Redis key
            default: Default value if key doesn't exist

        Returns:
            Deserialized Python object or default value
        """
        try:
            value = self.client.get(key)
            if value is None:
                return default
            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            print(f"Error getting JSON key {key}: {e}")
            return default

    # List Operations

    def append_to_list(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Append an item to a JSON list stored in Redis.

        Args:
            key: Redis key
            value: Item to append
            ttl: Reset TTL after append (default: 24 hours)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_list = self.get_json(key, default=[])
            if not isinstance(current_list, list):
                current_list = []
            current_list.append(value)
            return self.set_json(key, current_list, ttl)
        except Exception as e:
            print(f"Error appending to list {key}: {e}")
            return False

    def get_list(self, key: str) -> List[Any]:
        """
        Get a list from Redis.

        Args:
            key: Redis key

        Returns:
            List of items or empty list if key doesn't exist
        """
        result = self.get_json(key, default=[])
        return result if isinstance(result, list) else []

    # Key Management

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: Redis key to delete

        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            print(f"Error deleting key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: Redis key

        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            print(f"Error checking existence of key {key}: {e}")
            return False

    def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Set or update TTL for an existing key.

        Args:
            key: Redis key
            ttl: Time-to-live in seconds

        Returns:
            bool: True if TTL was set, False otherwise
        """
        try:
            return bool(self.client.expire(key, ttl))
        except RedisError as e:
            print(f"Error setting TTL for key {key}: {e}")
            return False

    def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Redis key

        Returns:
            int: TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except RedisError as e:
            print(f"Error getting TTL for key {key}: {e}")
            return -2

    # Batch Operations

    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """
        Get all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "session:*:chats")

        Returns:
            List of matching keys
        """
        try:
            return list(self.client.keys(pattern))
        except RedisError as e:
            print(f"Error getting keys by pattern {pattern}: {e}")
            return []

    def delete_by_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis pattern

        Returns:
            int: Number of keys deleted
        """
        try:
            keys = self.get_keys_by_pattern(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            print(f"Error deleting keys by pattern {pattern}: {e}")
            return 0


# Singleton instance for easy import
redis_client = RedisClient()
