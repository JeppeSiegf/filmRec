import os
import sys
import argparse
import logging
import importlib
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv(".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOG = logging.getLogger("enqueue")

# ── Celery app import ──────────────────────────────────────────────────────────
try:
    from worker.scraper.celery_app import app
except ImportError as e:
    LOG.error("Cannot import Celery app: %s", e)
    sys.exit(1)

# ── Task registration ──────────────────────────────────────────────────────────
try:
    importlib.import_module("worker.scraper.tasks")
except ImportError as e:
    LOG.error("Cannot import worker.scraper.tasks: %s", e)
    sys.exit(1)

try:
    app.autodiscover_tasks(["worker.scraper.tasks"])
except Exception:
    pass

LOG.info("Registered tasks: %s", [k for k in app.tasks if not k.startswith("celery.")])


# ── Core enqueue helper ────────────────────────────────────────────────────────
def enqueue(task_name: str, **kwargs) -> Dict[str, Any]:
    task = app.tasks.get(task_name)
    if not task:
        raise RuntimeError(f"Task '{task_name}' not registered. Known: {[k for k in app.tasks if not k.startswith('celery.')]}")
    result = task.apply_async(kwargs=kwargs)
    LOG.info("Enqueued %s id=%s kwargs=%s", task_name, result.id, kwargs)
    return {"task": task_name, "task_id": result.id, "kwargs": kwargs}


# ── Command handlers ───────────────────────────────────────────────────────────
def handle_test(argv):
    argparse.ArgumentParser(prog="test").parse_args(argv)
    return enqueue("test")


def handle_film(argv):
    p = argparse.ArgumentParser(prog="film")
    p.add_argument("user")
    p.add_argument("title")
    a = p.parse_args(argv)
    return enqueue("film", user=a.user, title=a.title)


def handle_filmRefs(argv):

    p = argparse.ArgumentParser(prog="filmRefs")
    p.add_argument("user")
    p.add_argument("title")
    p.add_argument("--use-stop-point", action="store_true")
    p.add_argument("--genres", type=int, nargs="+")
    p.add_argument("--decade", type=int)

    a = p.parse_args(argv)
    payload = {"user": a.user, "title": a.title, "use_stop_point": a.use_stop_point}
    if a.genres is not None: payload["genres"] = a.genres
    if a.decade is not None: payload["decade"] = a.decade
    return enqueue("filmRefs", **payload)


def handle_filmInfo(argv):
    p = argparse.ArgumentParser(prog="filmInfo")
    p.add_argument("film_refs", nargs="+")
    return enqueue("filmInfo", film_refs=p.parse_args(argv).film_refs)


def handle_user(argv):
    p = argparse.ArgumentParser(prog="user")
    p.add_argument("user")
    p.add_argument("--timespan")

    a = p.parse_args(argv)
    payload: Dict[str, Any] = {"user": a.user}
    if a.timespan is not None: payload["timespan"] = a.timespan

    return enqueue("user", **payload)


def handle_ratingsUser(argv):
    argparse.ArgumentParser(prog="ratingsUser").parse_args(argv)
    return enqueue("ratingsUser")


def handle_ratingsFilm(argv):
    p = argparse.ArgumentParser(prog="ratingsFilm")
    p.add_argument("film_refs", nargs="+")
    return enqueue("ratingsFilm", film_refs=p.parse_args(argv).film_refs)


def handle_ratings(argv):

    p = argparse.ArgumentParser(prog="ratings")
    p.add_argument("user")
    p.add_argument("--use-stop-point", action="store_true")
    p.add_argument("--update-log",     action="store_true")
    p.add_argument("--genres", type=int, nargs="+")
    p.add_argument("--decade", type=int)

    a = p.parse_args(argv)
    payload: Dict[str, Any] = {"user": a.user, "use_stop_point": a.use_stop_point, "update_log": a.update_log}

    if a.genres is not None: payload["genres"] = a.genres
    if a.decade is not None: payload["decade"] = a.decade

    return enqueue("ratings", **payload)


def handle_member(argv):
    p = argparse.ArgumentParser(prog="member")
    p.add_argument("film")
    p.add_argument("stop_page", type=int)
    p.add_argument("stop_user")
    p.add_argument("--add-new-users", action="store_true")

    a = p.parse_args(argv)
    if a.stop_page <= 0:
        p.error("stop_page must be > 0")
    payload: Dict[str, Any] = {"film": a.film, "stop_page": a.stop_page, "stop_user": a.stop_user, "addNewUsers": a.add_new_users}
    return enqueue("member", **payload)


# ── Dispatch ───────────────────────────────────────────────────────────────────
HANDLERS = {
    "test":        handle_test,
    "film":        handle_film,
    "filmRefs":    handle_filmRefs,
    "filmInfo":    handle_filmInfo,
    "user":        handle_user,
    "ratingsUser": handle_ratingsUser,
    "ratingsFilm": handle_ratingsFilm,
    "ratings":     handle_ratings,
    "member":      handle_member,
}


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("Available commands:\n  " + "\n  ".join(sorted(HANDLERS)))
        return 0

    handler = HANDLERS.get(argv[0])
    if not handler:
        print(f"Unknown command: {argv[0]}\nAvailable:\n  " + "\n  ".join(sorted(HANDLERS)))
        return 2

    try:
        print("Enqueued:", handler(argv[1:]))
        return 0
    except Exception as e:
        LOG.exception("Command '%s' failed: %s", argv[0], e)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())