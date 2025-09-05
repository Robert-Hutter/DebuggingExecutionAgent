# tracer.py
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from functools import wraps
from inspect import iscoroutinefunction, isfunction
from time import perf_counter_ns, process_time_ns
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type
import asyncio
import csv
import json
import threading

@dataclass
class Span:
    kind: str                 # "api" or "program"
    name: str                 # e.g., "Class.method", "module.fn", "entire_run"
    start_ns: int
    end_ns: int
    wall_ns: int              # end_ns - start_ns
    cpu_start_ns: int
    cpu_end_ns: int
    cpu_ns: int
    meta: Dict[str, Any]

class Tracer:
    """
    - Use @tracer.trace_api on the Python methods/functions you consider your 'API'.
    - Use with tracer.program(...) around your entire run.
    - Optional: tracer.instrument_class(...) or tracer.instrument_module(...) to auto-wrap many callables.
    """
    def __init__(self, run_id: str = "run", out_dir: str = "traces"):
        self.run_id = run_id
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._spans: List[Span] = []
        self._lock = threading.Lock()
        self._patches: List[Tuple[object, str, Callable]] = []  # (obj, attr, original)

    # ---------- Core span capture ----------
    @contextmanager
    def span(self, name: str, kind: str = "api", **meta):
        ws = perf_counter_ns(); cs = process_time_ns()
        try:
            yield
        finally:
            we = perf_counter_ns(); ce = process_time_ns()
            s = Span(kind=kind, name=name,
                     start_ns=ws, end_ns=we, wall_ns=we-ws,
                     cpu_start_ns=cs, cpu_end_ns=ce, cpu_ns=ce-cs,
                     meta=meta)
            with self._lock:
                self._spans.append(s)

    def api(self, name: str, **meta):
        return self.span(name=name, kind="api", **meta)

    def program(self, name: str = "entire_run", **meta):
        return self.span(name=name, kind="program", **meta)

    # ---------- Decorators (sync/async) ----------
    def trace_api(self, name: Optional[str] = None, **meta):
        """Decorator for sync or async functions/methods."""
        def deco(fn: Callable):
            label = name or fn.__qualname__
            if iscoroutinefunction(fn):
                @wraps(fn)
                async def awrap(*args, **kwargs):
                    ws = perf_counter_ns(); cs = process_time_ns()
                    try:
                        return await fn(*args, **kwargs)
                    finally:
                        we = perf_counter_ns(); ce = process_time_ns()
                        s = Span("api", label, ws, we, we-ws, cs, ce, ce-cs, dict(meta))
                        with self._lock:
                            self._spans.append(s)
                return awrap
            else:
                @wraps(fn)
                def wrap(*args, **kwargs):
                    ws = perf_counter_ns(); cs = process_time_ns()
                    try:
                        return fn(*args, **kwargs)
                    finally:
                        we = perf_counter_ns(); ce = process_time_ns()
                        s = Span("api", label, ws, we, we-ws, cs, ce, ce-cs, dict(meta))
                        with self._lock:
                            self._spans.append(s)
                return wrap
        return deco

    # ---------- Auto-instrumentation ----------
    def _wrap_callable(self, owner: object, attr: str, fn: Callable, name: Optional[str], **meta):
        label = name or getattr(fn, "__qualname__", attr)
        tracer = self

        if iscoroutinefunction(fn):
            @wraps(fn)
            async def awrap(*args, **kwargs):
                ws = perf_counter_ns(); cs = process_time_ns()
                try:
                    return await fn(*args, **kwargs)
                finally:
                    we = perf_counter_ns(); ce = process_time_ns()
                    s = Span("api", label, ws, we, we-ws, cs, ce, ce-cs, dict(meta))
                    with tracer._lock:
                        tracer._spans.append(s)
            wrapped = awrap
        else:
            @wraps(fn)
            def wrap(*args, **kwargs):
                ws = perf_counter_ns(); cs = process_time_ns()
                try:
                    return fn(*args, **kwargs)
                finally:
                    we = perf_counter_ns(); ce = process_time_ns()
                    s = Span("api", label, ws, we, we-ws, cs, ce, ce-cs, dict(meta))
                    with tracer._lock:
                        tracer._spans.append(s)
            wrapped = wrap

        # Patch and record for later restore
        original = getattr(owner, attr)
        setattr(owner, attr, wrapped)
        self._patches.append((owner, attr, original))

    def instrument_class(self, cls: Type, include: Optional[Iterable[str]] = None,
                         exclude: Iterable[str] = ("__init__", "__repr__", "__str__", "__eq__", "__hash__"),
                         name_prefix: Optional[str] = None, **meta):
        """
        Wraps public methods of a class in tracers. Call tracer.restore() to undo.
        include: names to include (overrides default public detection).
        """
        methods = include or [n for n in dir(cls) if not n.startswith("_")]
        for n in methods:
            if n in exclude: 
                continue
            obj = getattr(cls, n, None)
            if callable(obj):
                label = f"{name_prefix or cls.__name__}.{n}"
                self._wrap_callable(cls, n, obj, label, **meta)
        return self

    def instrument_module(self, mod: ModuleType, include: Optional[Iterable[str]] = None,
                          exclude: Iterable[str] = (), name_prefix: Optional[str] = None, **meta):
        """
        Wraps top-level functions of a module. Call tracer.restore() to undo.
        """
        names = include or [n for n in dir(mod) if not n.startswith("_")]
        for n in names:
            obj = getattr(mod, n, None)
            if isfunction(obj) and n not in exclude:
                label = f"{name_prefix or mod.__name__}.{n}"
                self._wrap_callable(mod, n, obj, label, **meta)
        return self

    def restore(self):
        """Undo auto-instrumentation patches."""
        while self._patches:
            owner, attr, original = self._patches.pop()
            setattr(owner, attr, original)

    # ---------- Export ----------
    def save(self) -> Dict[str, str]:
        csv_path = self.out_dir / f"{self.run_id}.csv"
        json_path = self.out_dir / f"{self.run_id}.json"
        fieldnames = ["kind","name","start_ns","end_ns","wall_ns","cpu_start_ns","cpu_end_ns","cpu_ns","meta"]
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for s in self._spans:
                row = asdict(s)
                row["meta"] = json.dumps(row["meta"], ensure_ascii=False)
                w.writerow(row)
        with json_path.open("w") as f:
            json.dump([asdict(s) for s in self._spans], f, ensure_ascii=False, indent=2)
        return {"csv": str(csv_path), "json": str(json_path)}