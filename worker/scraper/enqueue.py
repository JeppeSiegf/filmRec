# enqueue.py
import os
import sys
import argparse
from typing import List, Dict, Any, Optional

from celery import Celery
import worker.scraper.tasks

app = Celery(
    "scraper",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)
app.autodiscover_tasks(["worker.scraper.tasks"])


def enqueue(task_name: str, **kwargs) -> Dict[str, Any]:

    task = app.tasks.get(task_name)

    if not task:
        raise RuntimeError(f"Task '{task_name}' not registered in Celery")
    result = task.apply_async(kwargs=kwargs)
    return {"task": task_name, "task_id": result.id, "kwargs": kwargs}


def handle_test(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="test")
    p.parse_args(argv)
    return enqueue("test")

def handle_film(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="film")
    p.add_argument("user")
    p.add_argument("title")
    args = p.parse_args(argv)
    return enqueue("film", user=args.user, title=args.title)

def handle_filmRefs(argv: List[str]) -> Dict[str, Any]:
    # genres accepted as space-separated ints: --genres 1 2 3
    p = argparse.ArgumentParser(prog="filmRefs")
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
    p = argparse.ArgumentParser(prog="filmInfo")
    p.add_argument("film_refs", nargs="+", help="one or more film page_refs")
    args = p.parse_args(argv)
    return enqueue("filmInfo", film_refs=args.film_refs)


def handle_user(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="user")
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
    p = argparse.ArgumentParser(prog="ratingsUser")
    p.parse_args(argv)
    return enqueue("ratingsUser")


def handle_ratingsFilm(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="ratingsFilm")
    p.add_argument("film_refs", nargs="+")
    args = p.parse_args(argv)
    return enqueue("ratingsFilm", film_refs=args.film_refs)


def handle_ratings(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser(prog="ratings")
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
    p = argparse.ArgumentParser(prog="member")
    p.add_argument("film")
    p.add_argument("stop_page", type=int)
    p.add_argument("stop_user")
    p.add_argument("--add-new-users", action="store_true")
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


# -------------------------
# main: dispatch only; each case uses its own parser above
# -------------------------
def main():
    if len(sys.argv) < 2:
        print(os.getenv("CELERY_BROKER_URL"))
        print("Usage: python enqueue.py <task> [args...]")
        print("Tasks: test, update, film, filmRefs, filmInfo, user, ratingsUser, ratingsFilm, ratings, member")
        sys.exit(1)

    task = sys.argv[1]
    argv = sys.argv[2:]

    if task == "test":
        result = handle_test(argv)
    elif task == "film":
        result = handle_film(argv)
    elif task == "filmRefs":
        result = handle_filmRefs(argv)
    elif task == "filmInfo":
        result = handle_filmInfo(argv)
    elif task == "user":
        result = handle_user(argv)
    elif task == "ratingsUser":
        result = handle_ratingsUser(argv)
    elif task == "ratingsFilm":
        result = handle_ratingsFilm(argv)
    elif task == "ratings":
        result = handle_ratings(argv)
    elif task == "member":
        result = handle_member(argv)
    else:
        print(f"Unknown task or None Supported Task: {task}")
        sys.exit(2)

    print("Enqueued:", result)


if __name__ == "__main__":
    main()
