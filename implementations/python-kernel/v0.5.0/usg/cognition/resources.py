"""Measured local resource budgets; unavailable measurements fail conservatively."""
import ctypes
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResourceSnapshot:
    free_ram_mb: int | None
    free_disk_mb: int
    load_per_cpu: float | None

    def to_json(self):
        return asdict(self)


def snapshot(path='.'):
    memory=None
    try:
        if os.name=='nt':
            class Status(ctypes.Structure):
                _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
            status=Status();status.length=ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                memory=int(status.available//1048576)
        elif Path('/proc/meminfo').exists():
            rows=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
            memory=int(rows['MemAvailable'].split()[0])//1024
        elif hasattr(os,'sysconf'):
            memory=int(os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')//1048576)
    except (OSError,ValueError,KeyError,AttributeError):
        memory=None
    try:
        load=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
    except (OSError,AttributeError):
        load=None
    return ResourceSnapshot(memory,int(shutil.disk_usage(path).free//1048576),load)


def decide(measured,governor,*,input_chars=0,queued=0):
    if measured.free_disk_mb<64 or measured.load_per_cpu is not None and measured.load_per_cpu>4:
        return 'DEFER'
    # With no reliable memory reading, only the bounded rules path is enabled.
    mode=governor.plan(input_chars=input_chars,free_ram_mb=measured.free_ram_mb if measured.free_ram_mb is not None else 256,queued=queued)
    return mode
