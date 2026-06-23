from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RepairRecord
from app.schemas.ticket import RepairRecordUpdate


class RepairService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, record_id: int) -> RepairRecord | None:
        return self.db.get(RepairRecord, record_id)

    def list(
        self,
        *,
        asset_id: int | None = None,
        ticket_id: int | None = None,
        repair_user_id: int | None = None,
        repair_result: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[RepairRecord], int]:
        stmt = select(RepairRecord)
        if asset_id is not None:
            stmt = stmt.where(RepairRecord.asset_id == asset_id)
        if ticket_id is not None:
            stmt = stmt.where(RepairRecord.ticket_id == ticket_id)
        if repair_user_id is not None:
            stmt = stmt.where(RepairRecord.repair_user_id == repair_user_id)
        if repair_result:
            stmt = stmt.where(RepairRecord.repair_result == repair_result)
        if start_date:
            stmt = stmt.where(RepairRecord.repaired_at >= datetime.combine(start_date, time.min))
        if end_date:
            stmt = stmt.where(RepairRecord.repaired_at <= datetime.combine(end_date, time.max))

        total = len(list(self.db.scalars(stmt)))
        items = list(
            self.db.scalars(
                stmt.order_by(RepairRecord.repaired_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def update(self, record_id: int, payload: RepairRecordUpdate) -> RepairRecord | None:
        record = self.get(record_id)
        if record is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return record
