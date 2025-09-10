"""
MongoDB implementations of repository interfaces.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from ..domain.entities import AgentConfiguration, ConversationSession, MessageHistory, MessageRole
from ..domain.repositories import AgentConfigurationRepository, ConversationRepository
from .config import config


class MongoAgentConfigurationRepository(AgentConfigurationRepository):
    """MongoDB implementation of agent configuration repository."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.agent_configurations
    
    async def create_config(self, config_obj: AgentConfiguration) -> str:
        """Create a new agent configuration and return config_id."""
        config_dict = config_obj.dict()
        config_dict['_id'] = config_obj.config_id  # Use config_id as MongoDB _id
        
        await self.collection.insert_one(config_dict)
        return config_obj.config_id
    
    async def get_config(self, config_id: str) -> Optional[AgentConfiguration]:
        """Retrieve a configuration by ID."""
        doc = await self.collection.find_one({"_id": config_id})
        if not doc:
            return None
        
        # Remove MongoDB _id and restore config_id
        doc['config_id'] = doc.pop('_id')
        return AgentConfiguration(**doc)
    
    async def update_config(self, config_obj: AgentConfiguration) -> bool:
        """Update an existing configuration."""
        config_obj.updated_at = datetime.utcnow()
        config_dict = config_obj.dict()
        config_dict['_id'] = config_dict.pop('config_id')
        
        result = await self.collection.replace_one(
            {"_id": config_obj.config_id}, 
            config_dict
        )
        return result.modified_count > 0
    
    async def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        result = await self.collection.delete_one({"_id": config_id})
        return result.deleted_count > 0
    
    async def list_configs(self, active_only: bool = True) -> List[AgentConfiguration]:
        """List all configurations."""
        filter_query = {"active": True} if active_only else {}
        cursor = self.collection.find(filter_query).sort("created_at", -1)
        
        configs = []
        async for doc in cursor:
            doc['config_id'] = doc.pop('_id')
            configs.append(AgentConfiguration(**doc))
        
        return configs
    
    async def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists."""
        count = await self.collection.count_documents({"_id": config_id})
        return count > 0

    async def ensure_indexes(self):
        """Ensure proper indexes are created."""
        indexes = [
            IndexModel([("name", 1)]),
            IndexModel([("active", 1)]),
            IndexModel([("created_at", -1)])
        ]
        await self.collection.create_indexes(indexes)


class MongoConversationRepository(ConversationRepository):
    """MongoDB implementation of conversation repository."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.conversation_sessions
    
    async def create_session(self, session: ConversationSession) -> str:
        """Create a new conversation session and return session_id."""
        session_dict = session.dict()
        
        # Serialize LangChain messages
        session_dict['langchain_messages'] = self._serialize_messages(session.messages)
        session_dict.pop('messages')  # Remove the BaseMessage objects
        
        session_dict['_id'] = session.session_id  # Use session_id as MongoDB _id
        
        await self.collection.insert_one(session_dict)
        return session.session_id
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a session by ID."""
        doc = await self.collection.find_one({"_id": session_id})
        if not doc:
            return None
        
        # Remove MongoDB _id and restore session_id
        doc['session_id'] = doc.pop('_id')
        
        # Deserialize LangChain messages
        langchain_messages = doc.pop('langchain_messages', [])
        doc['messages'] = self._deserialize_messages(langchain_messages)
        
        return ConversationSession(**doc)
    
    async def update_session(self, session: ConversationSession) -> bool:
        """Update an existing session."""
        session.updated_at = datetime.utcnow()
        session_dict = session.dict()
        
        # Serialize LangChain messages
        session_dict['langchain_messages'] = self._serialize_messages(session.messages)
        session_dict.pop('messages')
        
        session_dict['_id'] = session_dict.pop('session_id')
        
        result = await self.collection.replace_one(
            {"_id": session.session_id}, 
            session_dict
        )
        return result.modified_count > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        result = await self.collection.delete_one({"_id": session_id})
        return result.deleted_count > 0
    
    async def list_sessions(self, config_id: Optional[str] = None, active_only: bool = True) -> List[ConversationSession]:
        """List sessions, optionally filtered by config_id."""
        filter_query = {}
        if config_id:
            filter_query["config_id"] = config_id
        if active_only:
            filter_query["active"] = True
        
        cursor = self.collection.find(filter_query).sort("created_at", -1)
        
        sessions = []
        async for doc in cursor:
            doc['session_id'] = doc.pop('_id')
            langchain_messages = doc.pop('langchain_messages', [])
            doc['messages'] = self._deserialize_messages(langchain_messages)
            sessions.append(ConversationSession(**doc))
        
        return sessions
    
    async def list_sessions_for_config(self, config_id: str) -> List[ConversationSession]:
        """List all sessions for a specific configuration."""
        return await self.list_sessions(config_id=config_id, active_only=False)
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        count = await self.collection.count_documents({"_id": session_id})
        return count > 0

    async def ensure_indexes(self):
        """Ensure proper indexes are created."""
        indexes = [
            IndexModel([("config_id", 1)]),
            IndexModel([("active", 1)]),
            IndexModel([("created_at", -1)]),
            IndexModel([("config_id", 1), ("created_at", -1)])
        ]
        await self.collection.create_indexes(indexes)
    
    def _serialize_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Serialize LangChain messages for MongoDB storage."""
        serialized = []
        for message in messages:
            msg_dict = {
                'type': message.__class__.__name__,
                'content': message.content,
                'additional_kwargs': getattr(message, 'additional_kwargs', {})
            }
            serialized.append(msg_dict)
        return serialized
    
    def _deserialize_messages(self, serialized: List[Dict[str, Any]]) -> List[BaseMessage]:
        """Deserialize LangChain messages from MongoDB storage."""
        messages = []
        for msg_dict in serialized:
            msg_type = msg_dict['type']
            content = msg_dict['content']
            additional_kwargs = msg_dict.get('additional_kwargs', {})
            
            if msg_type == 'HumanMessage':
                message = HumanMessage(content=content, additional_kwargs=additional_kwargs)
            elif msg_type == 'AIMessage':
                message = AIMessage(content=content, additional_kwargs=additional_kwargs)
            elif msg_type == 'SystemMessage':
                message = SystemMessage(content=content, additional_kwargs=additional_kwargs)
            else:
                # Fallback to HumanMessage for unknown types
                message = HumanMessage(content=content, additional_kwargs=additional_kwargs)
            
            messages.append(message)
        return messages


class MongoDBConnection:
    """Manages MongoDB connection and provides repository instances."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._config_repo: Optional[MongoAgentConfigurationRepository] = None
        self._conversation_repo: Optional[MongoConversationRepository] = None
    
    async def connect(self):
        """Establish MongoDB connection."""
        if not config.mongodb_url:
            raise ValueError("MongoDB URL not configured. Please set MONGODB_URL environment variable.")
        
        self.client = AsyncIOMotorClient(config.mongodb_url)
        self.database = self.client[config.mongodb_database]
        
        # Test connection
        await self.client.admin.command('ping')
        
        # Initialize repositories
        self._config_repo = MongoAgentConfigurationRepository(self.database)
        self._conversation_repo = MongoConversationRepository(self.database)
        
        # Ensure indexes
        await self._config_repo.ensure_indexes()
        await self._conversation_repo.ensure_indexes()
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
    
    @property
    def config_repository(self) -> MongoAgentConfigurationRepository:
        """Get the configuration repository instance."""
        if not self._config_repo:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._config_repo
    
    @property
    def conversation_repository(self) -> MongoConversationRepository:
        """Get the conversation repository instance."""
        if not self._conversation_repo:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._conversation_repo


# Global MongoDB connection instance
mongodb = MongoDBConnection()