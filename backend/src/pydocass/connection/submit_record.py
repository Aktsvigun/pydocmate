from typing import Literal
from sqlalchemy.exc import OperationalError
import time
import logging
from .database import structures, get_db

log = logging.getLogger(__name__)
def submit_record(
    table: Literal["responses", "feedback", "inputs"],
    retries: int = 3,
    delay: int = 2,
    **kwargs
):
    for attempt in range(retries):
        try:
            record = structures[table](**kwargs)
            with get_db() as db:
                if db is None:
                    log.error("Database connection not configured")
                    return
                db.add(record)
                db.commit()
                db.refresh(record)
        except OperationalError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
