from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Faq, FaqCategory, User, UserRole
from app.schemas.faq import FaqCreate, FaqUpdate

FAQ_CATEGORY_NAMES = {
    FaqCategory.COMPUTER.value: "电脑问题",
    FaqCategory.NETWORK.value: "网络问题",
    FaqCategory.PRINTER.value: "打印机问题",
    FaqCategory.ACCOUNT.value: "账号系统问题",
    FaqCategory.OTHER.value: "其他问题",
}
FAQ_CATEGORY_ORDER = [
    FaqCategory.COMPUTER,
    FaqCategory.NETWORK,
    FaqCategory.PRINTER,
    FaqCategory.ACCOUNT,
    FaqCategory.OTHER,
]


class FaqService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        *,
        current_user: User,
        keyword: str | None = None,
        category: FaqCategory | None = None,
        status: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Faq], int]:
        stmt = select(Faq)
        if current_user.role == UserRole.EMPLOYEE:
            stmt = stmt.where(Faq.status == 1)
        elif status is not None:
            stmt = stmt.where(Faq.status == status)
        if category is not None:
            stmt = stmt.where(Faq.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    Faq.title.like(pattern),
                    Faq.summary.like(pattern),
                    Faq.content.like(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(Faq.sort_order.asc(), Faq.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def create(self, payload: FaqCreate) -> Faq:
        faq = Faq(**payload.model_dump())
        faq.view_count = 0
        self.db.add(faq)
        self.db.commit()
        self.db.refresh(faq)
        return faq

    def get(self, faq_id: int) -> Faq | None:
        return self.db.get(Faq, faq_id)

    def detail(self, faq_id: int, current_user: User) -> Faq | None:
        faq = self.get(faq_id)
        if faq is None:
            return None
        if current_user.role == UserRole.EMPLOYEE and faq.status != 1:
            return None
        faq.view_count += 1
        self.db.commit()
        self.db.refresh(faq)
        return faq

    def update(self, faq_id: int, payload: FaqUpdate) -> Faq | None:
        faq = self.get(faq_id)
        if faq is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        data.pop("view_count", None)
        for field, value in data.items():
            setattr(faq, field, value)
        self.db.commit()
        self.db.refresh(faq)
        return faq

    def update_status(self, faq_id: int, status: int) -> Faq | None:
        faq = self.get(faq_id)
        if faq is None:
            return None
        faq.status = status
        self.db.commit()
        self.db.refresh(faq)
        return faq

    def delete(self, faq_id: int) -> bool:
        faq = self.get(faq_id)
        if faq is None:
            return False
        self.db.delete(faq)
        self.db.commit()
        return True

    def category_stats(self, current_user: User) -> list[dict[str, int | str]]:
        stmt = select(Faq.category, func.count(Faq.id)).group_by(Faq.category)
        if current_user.role == UserRole.EMPLOYEE:
            stmt = stmt.where(Faq.status == 1)
        counts = {str(category): count for category, count in self.db.execute(stmt).all()}
        return [
            {
                "category": category.value,
                "category_name": FAQ_CATEGORY_NAMES[category.value],
                "count": counts.get(category.value, 0),
            }
            for category in FAQ_CATEGORY_ORDER
        ]
