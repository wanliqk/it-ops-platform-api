from collections.abc import Iterator
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.routes.tickets import router as tickets_router
from app.db.base import Base
from app.models import Ticket, TicketCategory, TicketStatus
from app.models import __all__ as _model_exports
from app.services.ticket_service import TicketService
from app.utils.timezone import local_now

_ = _model_exports


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        session.add(TicketCategory(id=1, name="默认分类", code="default", status=1))
        session.commit()
        yield session
    finally:
        session.close()
        engine.dispose()


def add_ticket(
    session: Session,
    ticket_id: int,
    status: TicketStatus,
    *,
    overdue: bool = False,
) -> None:
    now = local_now()
    session.add(
        Ticket(
            id=ticket_id,
            ticket_no=f"TK{ticket_id:04d}",
            title=f"ticket-{ticket_id}",
            description="test",
            category_id=1,
            status=status,
            reporter_id=1,
            sla_response_deadline=now - timedelta(minutes=10) if overdue else None,
            sla_resolve_deadline=now - timedelta(minutes=5) if overdue else None,
        )
    )


def test_statistics_summary_returns_zero_when_no_ticket(db_session: Session) -> None:
    result = TicketService(db_session).statistics_summary()

    assert result.model_dump() == {
        "total": 0,
        "pending_assign": 0,
        "pending_accept": 0,
        "processing": 0,
        "pending_confirm": 0,
        "completed": 0,
        "closed": 0,
        "cancelled": 0,
        "overdue": 0,
    }


def test_statistics_summary_counts_statuses_and_fills_missing_zero(
    db_session: Session,
) -> None:
    add_ticket(db_session, 1, TicketStatus.PENDING)
    add_ticket(db_session, 2, TicketStatus.PENDING_ACCEPT)
    add_ticket(db_session, 3, TicketStatus.PROCESSING)
    add_ticket(db_session, 4, TicketStatus.PENDING_CONFIRM)
    add_ticket(db_session, 5, TicketStatus.COMPLETED)
    add_ticket(db_session, 6, TicketStatus.CLOSED)
    add_ticket(db_session, 7, TicketStatus.CANCELLED)
    db_session.commit()

    result = TicketService(db_session).statistics_summary()

    assert result.total == 7
    assert result.pending_assign == 1
    assert result.pending_accept == 1
    assert result.processing == 1
    assert result.pending_confirm == 1
    assert result.completed == 1
    assert result.closed == 1
    assert result.cancelled == 1
    assert result.overdue == 0


def test_statistics_summary_only_counts_active_overdue_tickets(db_session: Session) -> None:
    add_ticket(db_session, 1, TicketStatus.PENDING, overdue=True)
    add_ticket(db_session, 2, TicketStatus.PENDING_ACCEPT, overdue=True)
    add_ticket(db_session, 3, TicketStatus.PROCESSING, overdue=True)
    add_ticket(db_session, 4, TicketStatus.PENDING_CONFIRM, overdue=True)
    add_ticket(db_session, 5, TicketStatus.COMPLETED, overdue=True)
    add_ticket(db_session, 6, TicketStatus.CLOSED, overdue=True)
    add_ticket(db_session, 7, TicketStatus.CANCELLED, overdue=True)
    db_session.commit()

    result = TicketService(db_session).statistics_summary()

    assert result.total == 7
    assert result.overdue == 4


def test_statistics_summary_route_is_registered_before_ticket_detail() -> None:
    paths = [route.path for route in tickets_router.routes]

    assert "/statistics/summary" in paths
    assert paths.index("/statistics/summary") < paths.index("/{ticket_id}")
