"""Versioned, content-verified domain snapshots with bounded open-shard cache.

The registry remains authoritative for global IDs. Domain snapshots are derived
physical partitions, never a second ID allocator or independent truth store.
Publishing a snapshot is an atomic catalogue transaction after durable file write.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
from collections import OrderedDict
from ..util import canonical_json
from ..errors import StorageError


class DomainPartitions:
    def __init__(self,directory,max_open=2):
        if not 1<=max_open<=32:raise ValueError('open-shard budget')
        self.root=Path(directory).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.max_open=max_open;self.cache=OrderedDict();self.lock=threading.RLock()
        self.catalogue=sqlite3.connect(self.root/'catalogue.db',isolation_level=None,check_same_thread=False)
        self.catalogue.execute('PRAGMA synchronous=FULL')
        self.catalogue.executescript('''CREATE TABLE IF NOT EXISTS snapshot(domain TEXT,version INTEGER,digest TEXT,filename TEXT,PRIMARY KEY(domain,version)) STRICT;
        CREATE TABLE IF NOT EXISTS active(domain TEXT PRIMARY KEY,version INTEGER) STRICT;''')

    def publish(self,domain,version,records):
        if not isinstance(domain,str) or not domain or type(version) is not int or version<1:raise ValueError('domain/version')
        records=list(records)
        if len(records)>100000:raise ValueError('snapshot record budget')
        records.sort(key=lambda r:(r['space'],r['id']))
        keys=set()
        for r in records:
            if set(r)!={'space','id','body'} or type(r['id']) is not int or r['id']<=0 or not isinstance(r['space'],str):raise ValueError('global record reference')
            if (r['space'],r['id']) in keys:raise ValueError('duplicate global reference')
            keys.add((r['space'],r['id']))
        payload=canonical_json(records)
        if len(payload.encode('utf8'))>64*1024*1024:raise ValueError('snapshot byte budget')
        digest=hashlib.sha256(payload.encode('utf8')).hexdigest()
        filename=digest+'.db';target=self.root/filename
        with self.lock:
            old=self.catalogue.execute('SELECT digest FROM snapshot WHERE domain=? AND version=?',(domain,version)).fetchone()
            if old and old[0]!=digest:raise StorageError('snapshot versions are immutable')
            if not target.exists():
                import uuid
                temporary=self.root/(uuid.uuid4().hex+'.pending')
                try:
                    c=sqlite3.connect(temporary)
                    try:
                        c.execute('PRAGMA synchronous=FULL')
                        c.execute('CREATE TABLE record(space TEXT,id INTEGER,body TEXT NOT NULL CHECK(json_valid(body)),PRIMARY KEY(space,id)) STRICT')
                        c.executemany('INSERT INTO record VALUES(?,?,?)',[(r['space'],r['id'],canonical_json(r['body'])) for r in records]);c.commit()
                    finally:c.close()
                    os.replace(temporary,target)
                finally:
                    if temporary.exists():temporary.unlink()
            self.catalogue.execute('BEGIN IMMEDIATE')
            try:
                committed=self.catalogue.execute('SELECT digest FROM snapshot WHERE domain=? AND version=?',(domain,version)).fetchone()
                if committed and committed[0]!=digest:raise StorageError('concurrent snapshot version conflict')
                self.catalogue.execute('INSERT OR IGNORE INTO snapshot VALUES(?,?,?,?)',(domain,version,digest,filename))
                self.catalogue.execute('INSERT INTO active VALUES(?,?) ON CONFLICT(domain) DO UPDATE SET version=excluded.version',(domain,version))
                self.catalogue.execute('COMMIT')
            except BaseException:self.catalogue.execute('ROLLBACK');raise
        return digest

    def get(self,domain,space,id_,version=None):
        with self.lock:
            if version is None:
                row=self.catalogue.execute('SELECT version FROM active WHERE domain=?',(domain,)).fetchone()
                if row is None:return None
                version=row[0]
            row=self.catalogue.execute('SELECT filename,digest FROM snapshot WHERE domain=? AND version=?',(domain,version)).fetchone()
            if row is None:return None
            filename,digest=row
            if filename!=digest+'.db' or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise StorageError('invalid partition manifest')
            if filename not in self.cache:
                path=self.root/filename
                conn=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
                rows=conn.execute('SELECT space,id,body FROM record ORDER BY space,id').fetchall()
                content=[{'space':s,'id':n,'body':json.loads(b)} for s,n,b in rows]
                if hashlib.sha256(canonical_json(content).encode('utf8')).hexdigest()!=digest:
                    conn.close();raise StorageError('partition content hash mismatch')
                self.cache[filename]=conn
                while len(self.cache)>self.max_open:self.cache.popitem(last=False)[1].close()
            self.cache.move_to_end(filename)
            value=self.cache[filename].execute('SELECT body FROM record WHERE space=? AND id=?',(space,id_)).fetchone()
            return json.loads(value[0]) if value else None

    def close(self):
        for conn in self.cache.values():conn.close()
        self.cache.clear();self.catalogue.close()

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
