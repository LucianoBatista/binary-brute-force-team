"""Chat session management service."""

import uuid
from datetime import datetime
from typing import List, Dict, Optional
from project.app.services.redis_client import redis_client


class ChatService:
    """
    Service for managing chat sessions and messages in Redis.

    Provides CRUD operations for:
    - Chat sessions (create, get, delete)
    - Messages (add, retrieve)
    - User chat history
    """

    # Redis key patterns
    SESSION_CHATS_KEY = "session:{session_id}:chats"
    CHAT_METADATA_KEY = "chat:{chat_id}:metadata"
    CHAT_MESSAGES_KEY = "chat:{chat_id}:messages"
    FILE_DATA_KEY = "file:{file_id}:data"

    @staticmethod
    def generate_chat_id() -> str:
        """Generate a unique chat ID."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_file_id() -> str:
        """Generate a unique file ID."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())

    # Chat Operations

    def create_chat(self, session_id: str, title: Optional[str] = None) -> str:
        """
        Create a new chat session.

        Args:
            session_id: User session ID
            title: Optional chat title (default: "Chat {number}")

        Returns:
            str: New chat ID
        """
        chat_id = self.generate_chat_id()

        # Get existing chats for this session
        existing_chats = self.get_user_chats(session_id)
        chat_number = len(existing_chats) + 1

        # Create chat metadata
        metadata = {
            "chat_id": chat_id,
            "title": title or f"Chat {chat_number:03d}",
            "created_at": datetime.utcnow().isoformat(),
            "session_id": session_id
        }

        # Store metadata
        metadata_key = self.CHAT_METADATA_KEY.format(chat_id=chat_id)
        redis_client.set_json(metadata_key, metadata)

        # Initialize empty messages list
        messages_key = self.CHAT_MESSAGES_KEY.format(chat_id=chat_id)
        redis_client.set_json(messages_key, [])

        # Add to session's chat list
        session_key = self.SESSION_CHATS_KEY.format(session_id=session_id)
        redis_client.append_to_list(session_key, chat_id)

        return chat_id

    def get_chat_metadata(self, chat_id: str) -> Optional[Dict]:
        """
        Get chat metadata.

        Args:
            chat_id: Chat ID

        Returns:
            Dict with chat metadata or None if not found
        """
        metadata_key = self.CHAT_METADATA_KEY.format(chat_id=chat_id)
        return redis_client.get_json(metadata_key)

    def get_user_chats(self, session_id: str) -> List[Dict]:
        """
        Get all chats for a session.

        Args:
            session_id: User session ID

        Returns:
            List of chat metadata dicts (newest first)
        """
        session_key = self.SESSION_CHATS_KEY.format(session_id=session_id)
        chat_ids = redis_client.get_list(session_key)

        chats = []
        for chat_id in chat_ids:
            metadata = self.get_chat_metadata(chat_id)
            if metadata:
                chats.append(metadata)

        # Sort by created_at (newest first)
        chats.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return chats

    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat and all its messages.

        Args:
            chat_id: Chat ID to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        # Get metadata to find session_id
        metadata = self.get_chat_metadata(chat_id)
        if not metadata:
            return False

        session_id = metadata.get("session_id")

        # Delete metadata and messages
        metadata_key = self.CHAT_METADATA_KEY.format(chat_id=chat_id)
        messages_key = self.CHAT_MESSAGES_KEY.format(chat_id=chat_id)

        redis_client.delete(metadata_key)
        redis_client.delete(messages_key)

        # Remove from session's chat list
        if session_id:
            session_key = self.SESSION_CHATS_KEY.format(session_id=session_id)
            chat_ids = redis_client.get_list(session_key)
            if chat_id in chat_ids:
                chat_ids.remove(chat_id)
                redis_client.set_json(session_key, chat_ids)

        return True

    # Message Operations

    def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> Dict:
        """
        Add a message to a chat.

        Args:
            chat_id: Chat ID
            role: Message role ("user" or "assistant")
            content: Message text content
            media_url: Optional URL to image/video
            media_type: Optional media MIME type (e.g., "image/png", "video/mp4")

        Returns:
            Dict: The added message
        """
        message = {
            "role": role,
            "content": content,
            "media_url": media_url,
            "media_type": media_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        messages_key = self.CHAT_MESSAGES_KEY.format(chat_id=chat_id)
        redis_client.append_to_list(messages_key, message)

        return message

    def get_chat_messages(self, chat_id: str) -> List[Dict]:
        """
        Get all messages for a chat.

        Args:
            chat_id: Chat ID

        Returns:
            List of message dicts (chronological order)
        """
        messages_key = self.CHAT_MESSAGES_KEY.format(chat_id=chat_id)
        messages = redis_client.get_list(messages_key)
        return messages

    def get_last_message(self, chat_id: str) -> Optional[Dict]:
        """
        Get the last message in a chat.

        Args:
            chat_id: Chat ID

        Returns:
            Dict: Last message or None if chat is empty
        """
        messages = self.get_chat_messages(chat_id)
        return messages[-1] if messages else None

    # File Storage Operations

    def store_file_data(
        self,
        file_id: str,
        file_path: str,
        extracted_text: str,
        original_filename: str
    ) -> bool:
        """
        Store file metadata and extracted text.

        Args:
            file_id: Unique file identifier
            file_path: Path to uploaded file
            extracted_text: Text extracted from PDF
            original_filename: Original filename

        Returns:
            bool: True if successful
        """
        file_data = {
            "file_id": file_id,
            "file_path": file_path,
            "extracted_text": extracted_text,
            "original_filename": original_filename,
            "uploaded_at": datetime.utcnow().isoformat()
        }

        file_key = self.FILE_DATA_KEY.format(file_id=file_id)
        return redis_client.set_json(file_key, file_data)

    def get_file_data(self, file_id: str) -> Optional[Dict]:
        """
        Retrieve file data by file_id.

        Args:
            file_id: File identifier

        Returns:
            Dict: File data or None if not found
        """
        file_key = self.FILE_DATA_KEY.format(file_id=file_id)
        return redis_client.get_json(file_key)

    def delete_file_data(self, file_id: str) -> bool:
        """
        Delete file data from Redis.

        Args:
            file_id: File identifier

        Returns:
            bool: True if deleted
        """
        file_key = self.FILE_DATA_KEY.format(file_id=file_id)
        return redis_client.delete(file_key)

    # Session Management

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session ID

        Returns:
            bool: True if session has chats
        """
        session_key = self.SESSION_CHATS_KEY.format(session_id=session_id)
        return redis_client.exists(session_key)

    def clear_session(self, session_id: str) -> bool:
        """
        Clear all chats for a session.

        Args:
            session_id: Session ID to clear

        Returns:
            bool: True if successful
        """
        # Get all chats
        chats = self.get_user_chats(session_id)

        # Delete each chat
        for chat in chats:
            self.delete_chat(chat["chat_id"])

        # Delete session key
        session_key = self.SESSION_CHATS_KEY.format(session_id=session_id)
        return redis_client.delete(session_key)


# Singleton instance for easy import
chat_service = ChatService()
