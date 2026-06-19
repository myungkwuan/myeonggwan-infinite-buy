from datetime import datetime

from app import models


def get_or_create_config(db):
    """싱글톤(id=1) 앱 설정 조회/생성."""
    cfg = db.query(models.AppConfig).filter(models.AppConfig.id == 1).first()
    if not cfg:
        cfg = models.AppConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def touch(cfg):
    cfg.updated_at = datetime.utcnow()
