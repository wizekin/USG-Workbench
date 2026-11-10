"""Unattended, acceptance-gated upgrade with an automatic database rollback.

This is an explicit release command. The inbox worker cannot bless changed code.
"""
from pathlib import Path
from contextlib import closing
import sqlite3

from .autonomy import seal
from .errors import StorageError
from .foundation.install import install_foundation, verify_foundation
from .runtime import USG
from .storage.audit import verify_chain
from .storage.database import Database


def upgrade(path,backup):
    path=Path(path).resolve(strict=True);backup=Path(backup).resolve()
    if path==backup or backup.exists():
        raise ValueError('upgrade backup must be a new, different file')
    from .acceptance import run
    before=seal.compute_manifest()
    acceptance=run()
    if not acceptance['passed']:
        raise StorageError('new release failed offline acceptance')
    if seal.compute_manifest()!=before:
        raise StorageError('release files changed during acceptance')
    with Database(str(path)) as db:
        with db.read() as r:
            valid,_=verify_chain(r.query('SELECT * FROM audit_log ORDER BY seq'))
        if not valid or not db.integrity_check() or not verify_foundation(db):
            raise StorageError('existing installation failed integrity checks')
        # The recovery snapshot precedes any migration or seal change.
        with closing(sqlite3.connect(str(backup))) as destination:
            db.raw_unsafe_connection().backup(destination)
    try:
        with Database(str(path)) as db:
            migrations=db.migrate()
            install_foundation(db)
            if seal.compute_manifest()!=before:
                raise StorageError('release files changed before publication')
            seal.install_seal(db,reseal=True)
            service=USG(db,initialize=False)
            audit=service.audit_store()
            if not audit['ok']:
                raise StorageError('post-upgrade semantic audit failed')
    except BaseException:
        # All target connections have closed before restoring the snapshot.
        with closing(sqlite3.connect(str(backup))) as source, closing(sqlite3.connect(str(path))) as target:
            source.backup(target)
        raise
    return {'upgraded':True,'db':str(path),'backup':str(backup),'migrations':migrations,
            'acceptance_checks':len(acceptance['checks']),'audit':audit,'human_review_required':False}
