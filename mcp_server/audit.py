# mcp_server/audit.py

import datetime
import logging
from sqlalchemy.orm import Session
from db.models import AuditLog
 
logger = logging.getLogger(__name__)
 
 
def log_action(db: Session, agent_name: str, tool_name: str, payload: dict) -> None:
    """
    Persists an audit record to the database AND emits a log line.
    The caller is responsible for providing an active session and closing it.
    """
    entry = AuditLog(
        agent_name=agent_name,
        tool_name=tool_name,
        payload=payload,
        timestamp=datetime.datetime.utcnow(),
    )
 
    try:
        db.add(entry)
        db.commit()
        logger.info(
            "AUDIT | agent=%s tool=%s payload=%s",
            agent_name,
            tool_name,
            payload,
        )
    except Exception as exc:
        db.rollback()
        # Never let audit failures silently crash the request; log and continue
        logger.error("Audit log write failed: %s", exc)
 
