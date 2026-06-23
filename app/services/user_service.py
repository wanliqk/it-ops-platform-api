from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Asset, RepairRecord, Ticket, User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: UserCreate) -> User:
        data = payload.model_dump()
        password = data.pop("password")
        user = User(**data, password_hash=hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def list(
        self,
        *,
        keyword: str | None = None,
        role: str | None = None,
        status: int | None = None,
        department: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[User], int]:
        stmt = select(User)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(User.username.like(like), User.real_name.like(like), User.phone.like(like))
            )
        if role:
            stmt = stmt.where(User.role == role)
        if status is not None:
            stmt = stmt.where(User.status == status)
        if department:
            stmt = stmt.where(User.department == department)

        total = len(list(self.db.scalars(stmt)))
        items = list(
            self.db.scalars(
                stmt.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        )
        return items, total

    def update(self, user_id: int, payload: UserUpdate) -> User | None:
        user = self.get(user_id)
        if user is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_status(self, user_id: int, status: int) -> User | None:
        user = self.get(user_id)
        if user is None:
            return None
        user.status = status
        self.db.commit()
        self.db.refresh(user)
        return user

    def reset_password(self, user_id: int, new_password: str) -> User | None:
        user = self.get(user_id)
        if user is None:
            return None
        user.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def has_related_data(self, user_id: int) -> bool:
        checks = [
            select(Ticket.id).where(Ticket.reporter_id == user_id),
            select(Ticket.id).where(Ticket.handler_id == user_id),
            select(Asset.id).where(Asset.user_id == user_id),
            select(RepairRecord.id).where(RepairRecord.repair_user_id == user_id),
        ]
        return any(self.db.scalar(stmt.limit(1)) is not None for stmt in checks)

    def delete(self, user_id: int) -> bool:
        user = self.get(user_id)
        if user is None:
            return False
        self.db.delete(user)
        self.db.commit()
        return True
