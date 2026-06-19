from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.services.app_config import get_or_create_config, touch

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=schemas.ConfigOut)
def get_config(db: Session = Depends(get_db)):
    return get_or_create_config(db)


@router.put("", response_model=schemas.ConfigOut)
def update_config(payload: schemas.ConfigUpdate, db: Session = Depends(get_db)):
    cfg = get_or_create_config(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    touch(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg
