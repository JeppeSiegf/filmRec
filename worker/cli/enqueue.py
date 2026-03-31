# worker/cli/enqueue.py
import os
import sys
import argparse
import logging
import importlib
import traceback
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv(".env")

LOG = logging.getLogger("enqueue")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ---- Import the Celery app (use package-relative import when possible) ----
# Try relative import first (this file is inside package 'worker.cli')
try:
    # when installed as package, relative import is more robust
    from ..scraper.celery_app import app  # type: ignore
    LOG.debug("Imported app via relative import (..scraper.celery_app).")
except Exception as rel_err:
    # fallback to absolute import
    try:
        from worker.scraper.celery_app import app  # type: ignore
        LOG.debug("Imported app via absolute import (worker.scraper.celery_app).")
    except Exception as abs_err:
        LOG.error("Failed to import Celery app (relative error: %s; absolute error below)", rel_err)
        LOG.error(traceback.format_exc())
        raise RuntimeError("Cannot import Celery app (worker.scraper.celery_app). Fix packaging/imports.") from abs_err

# ---- Ensure tasks are executed so @app.task registers them ----
def import_tasks_and_show():

    try:
        # Prefer package-relative import when running as installed package
        importlib.import_module("worker.scraper.tasks")
        LOG.info("Imported worker.scraper.tasks successfully (absolute import).")
    except Exception as abs_exc:
        # Try relative import (when run inside package context)
        try:
            # Attempt to import via package-relative path (worker.cli -> ..scraper)
            # This will work when this module is loaded as part of the worker package.
            pkg_base = __package__  # should be 'worker.cli' when installed as package
            if pkg_base:
                rel_module = pkg_base.rsplit(".", 1)[0] + ".scraper.tasks" if "." in pkg_base else "worker.scraper.tasks"
            else:
                rel_module = "worker.scraper.tasks"
            importlib.import_module(rel_module)
            LOG.info("Imported worker.scraper.tasks successfully (relative fallback: %s).", rel_module)
        except Exception as rel_exc:
            LOG.error("Failed to import worker.scraper.tasks with both absolute and relative attempts.")
            LOG.error("Absolute import error (worker.scraper.tasks):\n%s", traceback.format_exc())
            LOG.error("PYTHONPATH / sys.path at time of failure:")
            for p in sys.path:
                LOG.error("  %s", p)
            # Reraise original absolute exception to make failure visible to user/CI
            raise ImportError("Failed to import worker.scraper.tasks; see logs above for traceback.") from abs_exc

# Try importing tasks now, loudly — don't swallow failures silently
import_tasks_and_show()

# optional autodiscover (harmless if tasks already imported)
try:
    app.autodiscover_tasks(["worker.scraper.tasks"])
except Exception:
    LOG.debug("autodiscover_tasks raised an error but continuing; tasks imported explicitly.")

# After importing, show registered non-celery tasks
_non_celery = [k for k in app.tasks.keys() if not k.startswith("celery.")]
LOG.info("Registered tasks on app (non-celery): %s", _non_celery)


# ---- enqueue helper ----
def enqueue(task_name: str, **kwargs) -> Dict[str, Any]:
    """Single place that touches Celery."""
    task = app.tasks.get(task_name)
    if not task:
        raise RuntimeError(
            f"Task '{task_name}' not registered in Celery. Registered keys: {list(app.tasks.keys())[:80]}"
        )
    result = task.apply_async(kwargs=kwargs)
    LOG.info("Enqueued %s id=%s kwargs=%s", task_name, result.id, kwargs)
    return {"task": task_name, "task_id": result.id, "kwargs": kwargs}


# ---- handlers (unchanged) ----
def handle_test(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="test", description="Run test task")
    p.parse_args(argv)
    return enqueue("test")


def handle_film(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="film", description="Fetch films list for user/title")
    p.add_argument("user", help="user identifier")
    p.add_argument("title", help="list title")
    args = p.parse_args(argv)
    return enqueue("film", user=args.user, title=args.title)


def handle_filmRefs(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="filmRefs", description="Fetch broad film refs list")
    p.add_argument("user")
    p.add_argument("title")
    p.add_argument("--use-stop-point", action="store_true")
    p.add_argument("--order", type=int, default=None)
    p.add_argument("--genres", type=int, nargs="+", default=None,
                   help="space-separated genre ids, e.g. --genres 1 2 3")
    p.add_argument("--decade", type=int, default=None)
    args = p.parse_args(argv)

    payload = {"user": args.user, "title": args.title, "use_stop_point": args.use_stop_point}
    if args.order is not None:
        payload["order"] = args.order
    if args.genres is not None:
        payload["genres"] = args.genres
    if args.decade is not None:
        payload["decade"] = args.decade
    return enqueue("filmRefs", **payload)


def handle_filmInfo(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="filmInfo", description="Fetch detailed film info for refs")
    p.add_argument("film_refs", nargs="+", help="one or more page_refs")
    args = p.parse_args(argv)
    return enqueue("filmInfo", film_refs=args.film_refs)


def handle_user(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="user", description="Fetch users list for a given user")
    p.add_argument("user")
    p.add_argument("--timespan", default=None)
    p.add_argument("--order", type=int, default=None)
    args = p.parse_args(argv)

    payload: Dict[str, Any] = {"user": args.user}
    if args.timespan is not None:
        payload["timespan"] = args.timespan
    if args.order is not None:
        payload["order"] = args.order
    return enqueue("user", **payload)


def handle_ratingsUser(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="ratingsUser", description="Fetch ratings for all users")
    p.parse_args(argv)
    return enqueue("ratingsUser")


def handle_ratingsFilm(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="ratingsFilm", description="Fetch ratings for given film refs")
    p.add_argument("film_refs", nargs="+")
    args = p.parse_args(argv)
    return enqueue("ratingsFilm", film_refs=args.film_refs)


def handle_ratings(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="ratings", description="Fetch ratings for a user")
    p.add_argument("user")
    p.add_argument("--use-stop-point", action="store_true")
    p.add_argument("--update-log", action="store_true")
    p.add_argument("--order", type=int, default=None)
    p.add_argument("--genres", type=int, nargs="+", default=None,
                   help="space-separated genre ids, e.g. --genres 4 6")
    p.add_argument("--decade", type=int, default=None)
    args = p.parse_args(argv)

    payload: Dict[str, Any] = {
        "user": args.user,
        "use_stop_point": args.use_stop_point,
        "update_log": args.update_log,
    }
    if args.order is not None:
        payload["order"] = args.order
    if args.genres is not None:
        payload["genres"] = args.genres
    if args.decade is not None:
        payload["decade"] = args.decade
    return enqueue("ratings", **payload)


def handle_member(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="member", description="Fetch members who rated a film")
    p.add_argument("film", help="film page_ref")
    p.add_argument("stop_page", type=int, help="stop page (int > 0)")
    p.add_argument("stop_user", help="user to stop at")
    p.add_argument("--add-new-users", action="store_true", help="add new users discovered")
    p.add_argument("--order", type=int, default=None)
    args = p.parse_args(argv)

    if args.stop_page <= 0:
        p.error("stop_page must be > 0")
    payload: Dict[str, Any] = {
        "film": args.film,
        "stop_page": args.stop_page,
        "stop_user": args.stop_user,
        "addNewUsers": args.add_new_users,
    }
    if args.order is not None:
        payload["order"] = args.order
    return enqueue("member", **payload)


HANDLERS = {
    "test": handle_test,
    "film": handle_film,
    "filmRefs": handle_filmRefs,
    "filmInfo": handle_filmInfo,
    "user": handle_user,
    "ratingsUser": handle_ratingsUser,
    "ratingsFilm": handle_ratingsFilm,
    "ratings": handle_ratings,
    "member": handle_member,
}


def print_available_tasks():
    print("Available commands:")
    for k in sorted(HANDLERS):
        print(f"  {k}")


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print_available_tasks()
        return 0

    cmd = argv[0]
    args = argv[1:]
    handler = HANDLERS.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}\n")
        print_available_tasks()
        return 2

    try:
        result = handler(args)
        print("Enqueued:", result)
        return 0

    except Exception as e:
        LOG.exception("Failed to run command %s: %s", cmd, e)
        print("Error:", e)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
