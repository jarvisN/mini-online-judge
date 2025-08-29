from __future__ import annotations

import json
import re
from functools import wraps
from typing import Any, Dict

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from problems import list_problems, get_problem
import grader


def create_app() -> Flask:
    app = Flask(__name__)

    # Basic config (adjust as needed)
    app.config["SECRET_KEY"] = "dev-secret-change-me"

    # Login policy: either whitelist or pattern (or both)
    # If ALLOWED_IDS is non-empty, it is enforced; otherwise ID_PATTERN is used
    app.config["ALLOWED_IDS"] = {"65001", "65002", "65003"}
    app.config["ID_PATTERN"] = r"^\d{5,10}$"

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "student_id" not in session:
                return redirect(url_for("login", next=request.path))
            return fn(*args, **kwargs)

        return wrapper

    @app.get("/login")
    def login():
        error = request.args.get("error")
        return render_template("login.html", error=error)

    @app.post("/login")
    def do_login():
        student_id = (request.form.get("student_id") or "").strip()
        allowed_ids = app.config.get("ALLOWED_IDS") or set()
        pattern = app.config.get("ID_PATTERN")

        ok = False
        if allowed_ids:
            ok = student_id in allowed_ids
        elif pattern:
            ok = re.match(pattern, student_id) is not None

        if not ok:
            return redirect(url_for("login", error="Invalid ID"))

        session["student_id"] = student_id
        return redirect(url_for("index"))

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        problems = list_problems()
        # Embed problems into the page for simple client-side switching
        return render_template(
            "index.html",
            problems=problems,
            problems_json=json.dumps(problems),
            student_id=session.get("student_id"),
        )

    @app.post("/api/run")
    @login_required
    def api_run():
        try:
            payload: Dict[str, Any] = request.get_json(force=True)
        except Exception:
            abort(400, description="Invalid JSON")

        problem_id = payload.get("problem_id")
        code = payload.get("code")
        if not isinstance(problem_id, str) or not isinstance(code, str):
            abort(400, description="Missing or invalid fields")

        problem = get_problem(problem_id)
        if not problem:
            abort(404, description="Problem not found")

        # Grade in an isolated process
        result = grader.run_in_subprocess(problem, code, time_limit=2.0, mem_limit_mb=128)

        return jsonify(result)

    return app


app = create_app()

if __name__ == "__main__":
    # For local development only
    app.run(host="127.0.0.1", port=5000, debug=True)

