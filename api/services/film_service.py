import asyncio
import os
import time
import traceback
import urllib.parse
from datetime import datetime, timedelta

import aiohttp
from sqlalchemy.orm.attributes import flag_modified

from api import create_app, db
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.models import Genre
from api.models.film import Film
from api.models.language import Language
from api.repositories.film_repository import FilmRepository
from api.services.crew_service import CrewService
from api.services.genre_service import GenreService


class FilmService:

    @staticmethod
    def get_all_films():

        films = FilmRepository.get_all_films()
        return films

    @staticmethod
    def get_film_by_page_ref(page_ref):

        film = FilmRepository.get_film_by_ref(page_ref)

        return film

    @staticmethod
    def get_newest_film():

        film = FilmRepository.get_newest_film()
        return film

    @staticmethod
    def search_films(query: str):

        search_result = FilmRepository.search_films(query)
        for result in search_result:
            result.image_ref_large = FilmService.proxify_image_url(result.image_ref_large)
        return search_result

    from datetime import datetime


    @staticmethod
    async def create_multiple_films(film_tuples):
        """
        Takes a list of tuples, maps them to the correct structure, and inserts them in bulk.
        Ensures that the first film's timestamp is the newest.
        """
        if not isinstance(film_tuples, list):
            raise TypeError("Expected a list of tuples.")

        film_data = [Film.map_film_simple(film_tuple) for film_tuple in film_tuples]

        # Step 2: Filter out None values (invalid mappings)
        film_data = [film for film in film_data if film is not None]

        if not film_data:
            print("No valid films to insert.")
            return []

        # Step 3: Ensure first film gets the newest timestamp


        # Step 4: Send to repository for bulk insert
        inserted_films = FilmRepository.bulk_insert_films(film_data)
        print(film_data[0]['page_ref'])
        await FilmService.update_film(film_data[0]['page_ref'],True)
        return inserted_films

    @staticmethod
    async def update_film(page_ref: str, timestamp=False):
        """
        Update a film with data collected from an external source.
        Uses a single session for all database operations.
        """
        try:
            # Get the film first to check if it exists
            existing_film = Film.query.filter_by(page_ref=page_ref).first()
            if not existing_film:
                print(f"Film {page_ref} not found.")
                return None

            # Fetch updated data via HTTP and extraction (async)
            collector = FilmDetailCollector(page_ref)
            await collector.fetch_page()
            await collector.extract_details()

            print("Extracted description:", collector.description)

            # Map the collected details into a dictionary
            updated_attributes = Film.map_film_detailed(collector)
            print("Mapped description:", updated_attributes.get('description'))

            # Update the film in the DB using the existing FilmRepository method,
            # but make sure it uses the same session
            updated_film = FilmRepository.update_film(page_ref, updated_attributes)

            if not updated_film:
                return None

            # If timestamp flag is False, update related entities
            # Using the same session as the updated film
            if not timestamp:
                if updated_attributes.get('genres'):
                    FilmRepository.update_film_genres(updated_film, updated_attributes['genres'])

                if updated_attributes.get('languages'):
                    FilmRepository.update_film_languages(updated_film, updated_attributes['languages'])

                if updated_attributes.get('crew'):
                    CrewService.add_film_credits_bulk(
                        film_ref=updated_film.page_ref,
                        crew_data=updated_attributes['crew']
                    )

                if updated_attributes.get('cast'):
                    CrewService.add_film_credits_bulk(
                        film_ref=updated_film.page_ref,
                        crew_data=updated_attributes['cast']
                    )

            return updated_film

        except Exception as e:
            db.session.rollback()
            print(f"Error updating film {page_ref}: {str(e)}")
            traceback.print_exc()
            return None

    @staticmethod
    async def update_multiple_films(film_refs: list[str]):
        """
        Update multiple films using a shared HTTP session.
        """
        await FilmDetailCollector.enable_shared_session()

        try:
            for film_ref in film_refs:
                await FilmService.update_film(film_ref)
        finally:
            await FilmDetailCollector.disable_shared_session()

    def __is_time_to_update(self, last_update: datetime.date, days: int):
        update_time = False
        current_date = datetime.now().date()
        if last_update is None:
            update_time = True
            return update_time

        if current_date - last_update > timedelta(days=days):
            update_time = True
            return update_time

        return update_time

    @staticmethod
    def delete_film(film_id):
        return FilmRepository.delete_film(film_id)

    @staticmethod
    @staticmethod
    def get_films_by_crew_member(crew_ref: str):
        # Fetch the credits associated with the crew member
        film_credits = CrewService.get_credits_by_crew_ref(crew_ref)

        # Extract film ids and roles
        film_ids = [credit.film_id for credit in film_credits]
        roles = {credit.film_id: [] for credit in film_credits}

        # Map each film_id to its corresponding roles
        for credit in film_credits:
            roles[credit.film_id].append(credit.role.role)

        # Fetch films by their ids
        films = FilmRepository.get_films_by_refs(film_ids)

        # Assign the list of roles to each film
        for film in films:
            film.roles = roles.get(film.page_ref, [])

        return films

    @staticmethod
    def filter_invalid_refs(film_refs):
        return FilmRepository.filter_invalid_refs(film_refs)

    @staticmethod
    def proxify_image_url(original_url: str) -> str:
        api_base = os.getenv("API_BASE_URL", "http://localhost:5000")  # adjust as needed
        encoded_url = urllib.parse.quote(original_url, safe='')
        return f"{api_base}/api/proxy/image?url={encoded_url}"

    @staticmethod
    def proxy_test():
        result = FilmService.search_films('barbi')
        for resu in result:
            print(resu.image_ref_large)


if __name__ == "__main__":
    import logging
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    app = create_app()
    with app.app_context():
       
        asyncio.run(FilmService.proxy_test())
