import asyncio
import os
import traceback
import urllib.parse

from api import create_app, db
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.models import Genre
from api.models.film import Film
from api.models.genre import film_genre
from api.models.language import film_language, Language
from api.repositories.film_repository import FilmRepository
from api.services.crew_service import CrewService
from api.services.utils.image_handler import ImageProxy


class FilmService:

    @staticmethod
    def get_all_films():

        films = FilmRepository.get_all_films()
        return films

    @staticmethod
    def get_film_by_page_ref(page_ref, with_crew):

        if with_crew is True:
            film = FilmRepository.get_film_by_ref_with_crew(page_ref)
        else:
            film = FilmRepository.get_film_by_ref_without_crew(page_ref)

        return film

    @staticmethod
    def get_films_by_refs(page_refs: list[str], with_crew):

        if with_crew is True:
            films = FilmRepository.get_films_by_refs_with_crew(page_refs)
        else:
            films = FilmRepository.get_films_by_refs_without_crew(page_refs)

        return films

    @staticmethod
    def get_newest_film():

        film = FilmRepository.get_newest_film()
        return film

    @staticmethod
    def search_films(query: str):

        search_result = FilmRepository.search_films(query)
        return search_result

    @staticmethod
    async def create_multiple_films(film_tuples):
        """
        Takes a list of tuples, maps them to the correct structure, and inserts them in bulk.
        Ensures that the first film's timestamp is the newest.
        """
        if not isinstance(film_tuples, list):
            raise TypeError("Expected a list of tuples.")

        film_data = [Film.map_film_simple(film_tuple) for film_tuple in film_tuples]

        film_data = [film for film in film_data if film is not None]

        if not film_data:
            print("No valid films to insert.")
            return []

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

            #TODO remove collector logic
            collector = FilmDetailCollector(page_ref)
            await collector.fetch_page()
            await collector.extract_details()

            print("Extracted description:", collector.description)

            # Map the collected details into a dictionary
            updated_attributes = Film.map_film_detailed(collector)
            print("Mapped description:", updated_attributes.get('description'))

            updated_film = FilmRepository.update_film(page_ref, updated_attributes)

            if not updated_film:
                return None
            # If timestamp flag is False, update related entities
            # Using the same session as the updated film
            if not timestamp:
                if updated_attributes.get('genres'):
                    FilmService.update_film_genres(updated_film, updated_attributes['genres'])

                if updated_attributes.get('languages'):
                    FilmService.update_film_languages(updated_film, updated_attributes['languages'])

                full_credits = []
                if updated_attributes.get('crew'):
                    full_credits.extend(updated_attributes['crew'])
                if updated_attributes.get('cast'):
                    full_credits.extend(updated_attributes['cast'])

                if full_credits:
                    CrewService.add_film_credits_bulk(
                        film_ref=updated_film.page_ref,
                        crew_data=full_credits
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

    @staticmethod
    def update_film_genres(existing_film, genres: list[str]):

        try:
            # Merge the film into the session.
            film = db.session.merge(existing_film)

            # Insert all genres; duplicates will be skipped by ON CONFLICT DO NOTHING.
            FilmRepository.bulk_insert_ignore_conflict(Genre, "genre", genres)

            # Query all Genre rows that match the provided names.
            genre_objs = FilmRepository.get_genres(genres)

            # Build new association entries.
            new_entries = [{'film_id': film.page_ref, 'genre_id': g.id} for g in genre_objs]

            # Bulk insert associations with ON CONFLICT DO NOTHING.
            FilmRepository.insert_association_entries(film_genre, new_entries)

            return genre_objs
        except Exception as e:
            db.session.rollback()
            print(f"Error updating film genres: {e}")
            raise

    @staticmethod
    def update_film_languages(existing_film, languages: list[dict]) -> list[dict]:

        try:
            # Validate input structure.
            if not isinstance(languages, list) or not all(
                    isinstance(lang, dict) and "name" in lang and "is_primary" in lang for lang in languages):
                raise ValueError(
                    "Invalid languages format. Expected list of dictionaries with 'name' and 'is_primary' keys.")

            language_names = [lang["name"] for lang in languages]
            FilmRepository.bulk_insert_ignore_conflict(Language, "language", language_names)

            # Get potential updated language list
            language_objs = FilmRepository.get_languages(language_names)

            # Build a mapping from language name to its object.
            lang_map = {l.language: l for l in language_objs}

            # Prepare association entries with the extra field.
            new_entries = [
                {"film_id": existing_film.page_ref,
                 "language_id": lang_map[lang["name"]].id,
                 "is_primary": lang["is_primary"]}
                for lang in languages if lang["name"] in lang_map
            ]

            # Bulk insert into the association table.
            FilmRepository.insert_association_entries(film_language, new_entries)

            return new_entries
        except Exception as e:
            db.session.rollback()
            print(f"Error updating film languages: {e}")
            raise e

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
        films = FilmRepository.get_films_by_refs_without_crew(film_ids)


        for film in films:
            film.roles = roles.get(film.page_ref, [])

        film_proxies = []

        for film in films:
            film_proxy = FilmService._get_image_proxies(film)
            film_proxies.append(film_proxy)

        return film_proxies


    @staticmethod
    def _get_image_proxies(film: Film):

        if film.image_ref:
            film.image_ref = ImageProxy.get_proxified_url(film.image_ref)
        if film.image_ref_large:
            film.image_ref_large = ImageProxy.get_proxified_url(film.image_ref_large)
        if film.banner_ref:
            film.banner_ref = ImageProxy.get_proxified_url(film.banner_ref)

        return film

    @staticmethod
    def update_series_id(series, film_refs: list[str]):

        if not film_refs:
            return


        if not series:
            print(f"Series with page_ref '{series.name}' not found.")
            return

        FilmRepository.update_series_ids(series, film_refs)




if __name__ == "__main__":
    app = create_app()
    with app.app_context():
       
        asyncio.run(FilmService.update_film('boogie-nights'))
