from __future__ import annotations

import ast
import multiprocessing as mp
import queue
import resource
import sys
import time
from typing import Any, Dict, List


# Strict but useful builtins whitelist
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "bytes": bytes,
    "callable": callable,
    "chr": chr,
    "complex": complex,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "getattr": getattr,
    "hasattr": hasattr,
    "hash": hash,
    "hex": hex,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "object": object,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "print": print,
    "range": range,
    "repr": repr,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


class SecurityError(Exception):
    pass


def _ensure_safe(code: str) -> None:
    """Parse AST to block imports and other obviously unsafe constructs."""
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise SecurityError(f"SyntaxError: {e.msg} (line {e.lineno})")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SecurityError("Import statements are not allowed")
        if isinstance(node, ast.Attribute):
            # Prevent dunder traversal like obj.__class__/__subclasses__ hacks
            if isinstance(node.attr, str) and node.attr.startswith("__"):
                raise SecurityError("Access to dunder attributes is not allowed")
        if isinstance(node, ast.Name):
            if node.id in {"__import__", "eval", "exec", "open"}:
                raise SecurityError(f"Usage of '{node.id}' is not allowed")


def _limit_resources(mem_limit_mb: int) -> None:
    # Best-effort resource limits (POSIX only)
    try:
        # CPU time hard limit (seconds): enforced by parent join as well
        # Here we keep it high and rely on wall clock; some systems enforce CPU only
        resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    except Exception:
        pass
    try:
        # Address space limit (MB)
        mem_bytes = mem_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except Exception:
        pass


def _execute(problem: Dict[str, Any], code: str, mem_limit_mb: int, out_q: mp.Queue) -> None:
    start = time.time()
    try:
        _limit_resources(mem_limit_mb)
        _ensure_safe(code)

        # Prepare execution namespace with safe builtins only
        ns: Dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
        exec(code, ns, ns)

        fname = problem["function_name"]
        if fname not in ns:
            raise SecurityError(f"Function '{fname}' is not defined")
        fn = ns[fname]

        tests: List[Dict[str, Any]] = []
        for idx, t in enumerate(problem["tests"], 1):
            args = t.get("args", [])
            kwargs = t.get("kwargs", {})
            expected = t.get("expected")
            item: Dict[str, Any] = {
                "index": idx,
                "args": args,
                "kwargs": kwargs,
                "expected": expected,
            }
            try:
                got = fn(*args, **kwargs)
                ok = False
                if isinstance(expected, list):
                    ok = any(got == e for e in expected)
                else:
                    ok = got == expected
                item.update({"ok": bool(ok), "got": got, "error": None})
            except Exception as e:  # noqa: BLE001
                item.update({"ok": False, "got": None, "error": f"ERROR: {type(e).__name__}: {e}"})
            tests.append(item)

        elapsed = time.time() - start
        out_q.put({
            "status": "ok",
            "tests": tests,
            "elapsed": round(elapsed, 4),
            "summary": {
                "total": len(tests),
                "passed": sum(1 for t in tests if t["ok"]),
            },
        })
    except SecurityError as se:
        out_q.put({"status": "error", "error": str(se)})
    except Exception as e:  # noqa: BLE001
        out_q.put({"status": "error", "error": f"ERROR: {type(e).__name__}: {e}"})


def run_in_subprocess(problem: Dict[str, Any], code: str, time_limit: float = 2.0, mem_limit_mb: int = 128) -> Dict[str, Any]:
    """Run user code in a separate process with time/memory limits.

    Returns a dict with either:
    - {status: "ok", tests: [...], elapsed: float, summary: {...}}
    - {status: "error", error: str}
    - {status: "tle"}
    """
    q: mp.Queue = mp.Queue()
    proc = mp.Process(target=_execute, args=(problem, code, mem_limit_mb, q))
    proc.start()
    proc.join(timeout=time_limit)

    if proc.is_alive():
        try:
            proc.terminate()
        finally:
            proc.join(0.1)
        return {"status": "tle", "error": "Time Limit Exceeded"}

    try:
        result = q.get_nowait()
    except queue.Empty:
        result = {"status": "error", "error": "No result returned"}
    return result
