import asyncio
import logging
import os
import random
import time
from typing import Union, Tuple, List, Dict

from celery import chain

from dataCollectors.utils.sort_categories import FilmSorting, GenreFilter, ReleaseDateFilter, TimePeriodSort, \
    UserSorting, RatingSorting, SingleRatingFilter, RatingRangeFilter
from app import app
from util.update_log import UpdateLog
from util.request import APIService
import util.lazy_import as imp

logger = logging.getLogger(__name__)


chunk_size = 100
max_tasks_per_minute: int = 500
queue = 'scraper'


@app.task(name='test',queue=queue)
def test():
    logger.info("sup")

@app.task(name='update',queue=queue)
def update_database(user: str, title: str):

    c = chain(
        fetch_films.s(user, title),
        fetch_ratings_for_films.s(),
        fetch_ratings_for_all_users.si()
    )

    async_result = c.apply_async()
    logger.info(f"Started chain for user={user}, title={title}; chain id: {async_result.id}")

    return {'chain_id': async_result.id, 'status': 'started'}



@app.task(name='film',queue=queue)
def fetch_films(user: str, title: str,):

    update_logger = UpdateLog(os.getenv("UPDATELOG_URL"))
    logger.info(f'stopping at : {update_logger.get(title)}')
    films = fetch_film_refs(user, title, order = FilmSorting.LAST_ADDITION, use_stop_point = True)

    if not films:
        logger.info("No films returned from fetch_films.")
        return []

    film_refs = [item['page_ref'] for item in films]
    chunks = [film_refs[i:i + chunk_size] for i in range(0, len(film_refs), chunk_size)]

    for chunk in chunks:
        fetch_film_info.delay(chunk)

    newest_entry = film_refs[0]
    update_logger.log(title, 'list', newest_entry)

    logger.info(f"Dispatched {len(chunks)} fetch_film_info tasks.")
    return film_refs


@app.task(name='filmRefs',queue=queue)
def fetch_film_refs(user: str, title: str,
                    decade: ReleaseDateFilter = None, genres: list[GenreFilter] = [],
                    order: FilmSorting = None, use_stop_point: bool = False):

    stopping_point = None
    if use_stop_point is True:
        update_logger = UpdateLog(os.getenv("UPDATELOG_URL"))
        stopping_point = update_logger.get(title)
        logger.info(f'Stopping point from broad list {stopping_point}')

    collector = imp.FilmListCollector(user, title, stopping_point)
    asyncio.run(collector.fetch_film_list(decade=decade, genres=genres, order=order))

    if collector.items is not None and len(collector.items) > 0:
        for i in range(0, len(collector.items), chunk_size):
            chunk = collector.items[i:i + chunk_size]
            api_service = APIService()
            asyncio.run(api_service.post_films(chunk))
        return collector.items

    logger.info("No films found")
    return []

@app.task(name='filmInfo',queue=queue)
def fetch_film_info(film_refs):

    if not film_refs:
        logger.info("No film refs provided.")
        return

    collector = imp.FilmDetailCollector()
    films = asyncio.run(fetch_page_info(film_refs, collector, 50))

    if films:
        api_service = APIService()
        asyncio.run(api_service.put_films(films))
    else:
        logger.info("No films to send.")


async def fetch_page_info(film_refs, collector: imp.PageCollector, sem: int) -> List[Dict]:
    await collector.enable_shared_session()

    sem = asyncio.Semaphore(sem)

    # Create tasks
    tasks = [
        _fetch_and_extract(ref, sem, collector)
        for ref in film_refs
    ]

    results = await asyncio.gather(*tasks, return_exceptions=False)
    await collector.disable_shared_session()

    return [r for r in results if r is not None]


async def _fetch_and_extract(
        film_ref: str,
        sem: asyncio.Semaphore,
        collector_cls: imp.PageCollector) -> dict | None:
    # This async with uses the shared semaphore
    async with sem:
        max_retries = 9
        initial_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                collector = collector_cls(film_ref)
                await collector.fetch_page()
                await collector.extract_details()

                # Check if title is None or invalid
                if collector.data and collector.data.get('title') is not None:
                    logger.info(collector.data.get('title'))
                    return collector.data
                else:
                    raise ValueError("Title returned None")

            except Exception as e:
                if attempt == max_retries:
                    print(f"[ERROR] Failed to collect for {film_ref} after {max_retries} attempts: {e}")
                    return None

                # Exponential backoff with jitter
                delay = initial_delay * (2 ** attempt) * (0.9 + 0.2 * random.random())
                print(f"[WARNING] Attempt {attempt + 1} failed for {film_ref}, retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)

        return None


@app.task(name='user',queue=queue)
def fetch_users(user, timespan: TimePeriodSort = None, order: UserSorting = None):

    collector = imp.UserListCollector(user)
    asyncio.run(collector.fetch_users_list(timespan=timespan, order=order))

    if collector.items is not None and len(collector.items) > 0:
        api_service = APIService()
        result = asyncio.run(api_service.test())
        logger.info(result)


@app.task(name='ratingsUser',queue=queue)
def fetch_ratings_for_all_users():

    try:
        update_logger = UpdateLog(os.getenv("UPDATELOG_URL"))
        users = update_logger.get_all('user')
        user_refs = list(users.keys())

        logger.info(user_refs[0])

        if not user_refs:
            logger.info("No users found to process")
            return {'users_processed': 0, 'tasks_launched': []}

        logger.info(f"Processing {len(user_refs)} users in chunks of {chunk_size}")

        tasks_launched = []

        # Process users in chunks for better rate limiting
        for i in range(0, len(user_refs), chunk_size):
            chunk = user_refs[i:i + chunk_size]

            # Launch chunk as a group
            chunk_tasks = []
            for user_id in chunk:
                task = fetch_ratings.delay(
                    user_id,
                    use_stop_point=True,
                    update_log=True,
                    order=RatingSorting.LAST_ADDITION.value
                )
                chunk_tasks.append({'task_id': task.id, 'user_id': user_id})

            tasks_launched.extend(chunk_tasks)

            logger.info(f"Launched chunk {i // chunk_size + 1}: {len(chunk)} tasks")

            # Rate limiting - sleep based on desired tasks per minute
            if (i + chunk_size) < len(user_refs):
                sleep_time = (60 / max_tasks_per_minute) * chunk_size
                time.sleep(sleep_time)

    except Exception as e:
        logger.error(f"Error processing users: {e}")
        raise

    logger.info(f"Launched {len(tasks_launched)} rating fetch tasks")
    return {
        'users_processed': len(tasks_launched),
        'tasks_launched': tasks_launched
    }

@app.task(name='ratingsFilm',queue=queue)
def fetch_ratings_for_films(film_refs):

    tasks_launched = []
    # Process users in chunks for better rate limiting
    for i in range(0, len(film_refs), chunk_size):
        chunk = film_refs[i:i + chunk_size]

        # Launch chunk as a group
        chunk_tasks = []
        for film_id in chunk:
            task = fetch_members.delay(
                film = film_id,
                stop_page=30,
                stop_user='aboutlalalala',
                order=UserSorting.POPULARITY.value
            )
            chunk_tasks.append({'task_id': task.id, 'film_id': film_id})

        tasks_launched.extend(chunk_tasks)

        logger.info(f"Launched chunk {i // chunk_size + 1}: {len(chunk)} tasks")

        # Rate limiting - sleep based on desired tasks per minute
        if (i + chunk_size) < len(film_refs):
            sleep_time = (60 / max_tasks_per_minute) * chunk_size
            time.sleep(sleep_time)

    logger.info(f"Launched {len(tasks_launched)} member fetch tasks")
    return {
        'films_processed': len(tasks_launched),
        'tasks_launched': tasks_launched
    }


@app.task(name='ratings',queue=queue)
def fetch_ratings(user: str, use_stop_point: bool = False, update_log=False, decade: ReleaseDateFilter = None,
                  genres: list[GenreFilter] = [], order = None):
    stopping_point = None

    if use_stop_point is True:
        update_logger = UpdateLog(os.getenv("UPDATELOG_URL"))
        stopping_point = update_logger.get(user)
        logger.info(stopping_point)

    collector = imp.RatingsCollector(user, stopping_point)
    asyncio.run(collector.fetch_ratings_list(decade=decade, genres=genres, order=RatingSorting.LAST_ADDITION))
    logger.info(collector.items)
    if collector.items is not None and len(collector.items) > 0:
        api_service = APIService()
        result = asyncio.run(api_service.post_ratings(collector.items))
        logger.info(result)

        if update_log is True:
            update_logger = UpdateLog(os.getenv("UPDATELOG_URL"))
            newest_entry = collector.items[0]
            update_logger.log(user, 'user', newest_entry.get('film_id'))
            logger.info("logged well")

    logger.info(collector.items)



@app.task(name='member',queue=queue)
def fetch_members(film, stop_page, stop_user,addNewUsers = False, ratings: Union[SingleRatingFilter,
Tuple[RatingRangeFilter, RatingRangeFilter]] = None,
                  order: UserSorting = None):

    collector = imp.MemberListCollector(film, stop_page, stop_user)
    asyncio.run(collector.fetch_member_list(ratings=ratings, order=order))

    if collector.items is not None and len(collector.items) > 0:
        # Users First
        if addNewUsers:
            api_service = APIService()
            asyncio.run(api_service.test())
        # Then Ratings
        api_service = APIService()
        asyncio.run(api_service.post_ratings(collector.ratings))

    logger.info(collector.items)



@app.task
def fetch_series():
    pass


@app.task
def fetch_themes():
    pass


@app.task
def fetch_tag():
    pass
