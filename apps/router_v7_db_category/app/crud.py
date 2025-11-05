from sqlalchemy.orm import Session as DbSession
from . import models

def get_session(db: DbSession, chat_id: str):
    return db.query(models.Session).filter(models.Session.chat_id == chat_id).first()

def create_session(db: DbSession, chat_id: str, data: dict):
    db_session = models.Session(chat_id=chat_id, data=data)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_session(db: DbSession, chat_id: str, data: dict):
    db_session = get_session(db, chat_id)
    if db_session:
        existing_data = db_session.data.copy()
        existing_data.update(data)
        db_session.data = existing_data
    else:
        db_session = models.Session(chat_id=chat_id, data=data)
        db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session