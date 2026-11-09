import os
import tempfile

from usg.storage.database import Database
from usg.util import FakeClock


def make_db(file: bool = False, clock=None):
    clock = clock or FakeClock()
    if file:
        d = tempfile.mkdtemp(prefix="usg_test_")
        db = Database(os.path.join(d, "t.db"), clock=clock)
    else:
        db = Database(":memory:", clock=clock)
    db.migrate()
    return db, clock
