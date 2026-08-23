from sqlalchemy.ext.asyncio import AsyncSession

from app.models.misc import AuditLog


async def audit(db: AsyncSession, action: str, actor_id: str | None = None,
                 entity_type: str | None = None, entity_id: str | None = None,
                 meta: dict | None = None) -> None:
    db.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type,
                     entity_id=entity_id, meta=meta or {}))
