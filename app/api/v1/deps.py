from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.utils.permissions import get_current_user, require_permissions, require_roles

DBSession = Annotated[Session, Depends(get_db)]

__all__ = ["DBSession", "get_current_user", "require_permissions", "require_roles"]
