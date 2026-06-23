from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Asset, AssetCategory, RepairRecord, Ticket, User
from app.schemas.asset import AssetCategoryCreate, AssetCategoryUpdate, AssetCreate, AssetUpdate


class AssetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: AssetCreate) -> Asset:
        asset = Asset(**payload.model_dump())
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get(self, asset_id: int) -> Asset | None:
        return self.db.get(Asset, asset_id)

    def get_by_asset_no(self, asset_no: str) -> Asset | None:
        return self.db.scalar(select(Asset).where(Asset.asset_no == asset_no))

    def list(
        self,
        *,
        keyword: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
        department: str | None = None,
        user_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Asset], int]:
        stmt = select(Asset)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    Asset.asset_no.like(like),
                    Asset.asset_name.like(like),
                    Asset.brand.like(like),
                    Asset.model.like(like),
                    Asset.serial_no.like(like),
                )
            )
        if category_id is not None:
            stmt = stmt.where(Asset.category_id == category_id)
        if status:
            stmt = stmt.where(Asset.status == status)
        if department:
            stmt = stmt.where(Asset.department == department)
        if user_id is not None:
            stmt = stmt.where(Asset.user_id == user_id)

        total = len(list(self.db.scalars(stmt)))
        items = list(
            self.db.scalars(
                stmt.order_by(Asset.id.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        )
        return items, total

    def update(self, asset_id: int, payload: AssetUpdate) -> Asset | None:
        asset = self.get(asset_id)
        if asset is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(asset, field, value)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update_status(self, asset_id: int, status: str, remark: str | None = None) -> Asset | None:
        asset = self.get(asset_id)
        if asset is None:
            return None
        asset.status = status
        if remark:
            asset.remark = remark
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete(self, asset_id: int) -> bool:
        asset = self.get(asset_id)
        if asset is None:
            return False
        self.db.delete(asset)
        self.db.commit()
        return True

    def has_tickets_or_repairs(self, asset_id: int) -> bool:
        return (
            self.db.scalar(select(Ticket.id).where(Ticket.asset_id == asset_id).limit(1))
            is not None
            or self.db.scalar(
                select(RepairRecord.id).where(RepairRecord.asset_id == asset_id).limit(1)
            )
            is not None
        )

    def category_exists(self, category_id: int) -> bool:
        return self.db.get(AssetCategory, category_id) is not None

    def user_exists(self, user_id: int | None) -> bool:
        return user_id is None or self.db.get(User, user_id) is not None


class AssetCategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: AssetCategoryCreate) -> AssetCategory:
        category = AssetCategory(**payload.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get(self, category_id: int) -> AssetCategory | None:
        return self.db.get(AssetCategory, category_id)

    def get_by_code(self, category_code: str) -> AssetCategory | None:
        return self.db.scalar(
            select(AssetCategory).where(AssetCategory.category_code == category_code)
        )

    def list(
        self,
        *,
        keyword: str | None = None,
        status: int | None = None,
    ) -> list[AssetCategory]:
        stmt = select(AssetCategory)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(AssetCategory.category_name.like(like), AssetCategory.category_code.like(like))
            )
        if status is not None:
            stmt = stmt.where(AssetCategory.status == status)
        return list(self.db.scalars(stmt.order_by(AssetCategory.id.asc())))

    def update(self, category_id: int, payload: AssetCategoryUpdate) -> AssetCategory | None:
        category = self.get(category_id)
        if category is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def has_assets(self, category_id: int) -> bool:
        return (
            self.db.scalar(select(Asset.id).where(Asset.category_id == category_id).limit(1))
            is not None
        )

    def delete(self, category_id: int) -> bool:
        category = self.get(category_id)
        if category is None:
            return False
        self.db.delete(category)
        self.db.commit()
        return True
