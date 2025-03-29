import os
from contextlib import contextmanager
import json
import logging
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    TypeDecorator,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

db_connection = str(os.getenv("DB_CONNECTION", None))
if db_connection is not None and db_connection != "None":
    engine = create_engine(db_connection, pool_pre_ping=True, pool_recycle=3600)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

Base = declarative_base()

log = logging.getLogger(__name__)
@contextmanager
def get_db():
    if SessionLocal is None:
        log.error("Database connection not configured")
        yield
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


class SetType(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(list(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return set()
        return set(json.loads(value))


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    in_code = Column(String)
    out_code = Column(String)
    in_time = Column(DateTime(timezone=True))
    out_time = Column(DateTime(timezone=True))
    annotations_id = Column(String, default=None)
    annotations_created_at = Column(DateTime(timezone=True), default=func.now())
    annotations_model = Column(String, default=None)
    annotations_completion_tokens = Column(Integer, default=0)
    annotations_prompt_tokens = Column(Integer, default=0)
    annotations_output = Column(String, default=None)
    annotations_required_imports = Column(SetType, default=None)
    docstrings_id = Column(String, default=None)
    docstrings_created_at = Column(DateTime(timezone=True), default=func.now())
    docstrings_model = Column(String, default=None)
    docstrings_completion_tokens = Column(Integer, default=0)
    docstrings_prompt_tokens = Column(Integer, default=0)
    docstrings_output = Column(String, default=None)
    comments_id = Column(String, default=None)
    comments_created_at = Column(DateTime(timezone=True), default=func.now())
    comments_model = Column(String, default=None)
    comments_completion_tokens = Column(Integer, default=0)
    comments_prompt_tokens = Column(Integer, default=0)
    comments_output = Column(String, default=None)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)

    in_code = Column(String)
    out_code = Column(String)
    in_time = Column(DateTime(timezone=True))
    out_time = Column(DateTime(timezone=True))
    is_good = Column(Boolean)


class Inputs(Base):
    __tablename__ = "inputs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    in_code = Column(String)
    in_time = Column(DateTime(timezone=True))


structures = {
    "responses": Response,
    "feedback": Feedback,
    "inputs": Inputs,
}
