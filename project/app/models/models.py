from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AgentExecution(Base):
    """
    Model to track agent execution history.

    This table stores information about each agent execution,
    including the query, result, and execution status.
    """
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False, comment="User query")
    result = Column(Text, nullable=True, comment="Agent execution result")
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        comment="Execution status: pending/completed/failed"
    )
    task_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Celery task ID for async executions"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when execution was created"
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Timestamp when execution completed"
    )

    def __repr__(self):
        return f"<AgentExecution(id={self.id}, status={self.status}, query='{self.query[:50]}...')>"
