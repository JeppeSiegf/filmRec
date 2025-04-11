import asyncio
import traceback

from api import create_app, db
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.models import Genre
from api.models.film import Film
from api.models.genre import film_genre
from api.models.language import Film_Language, Language
from api.repositories.film_repository import FilmRepository
from api.services.crew_service import CrewService
from api.services.genre_service import GenreService
from api.services.language_service import LanguageService
from api.services.utils.image_handler import ImageProxy


class FilmService:

    def __init__(self):
        self.repo = FilmRepository()
        self.genre_service = GenreService()
        self.lang_service = LanguageService()
        self.crew_service = CrewService()

        # TODO use
        self.image_attrs = ['image_ref','image_ref_large','banner_ref']


    def get_all_films(self):

        films = self.repo.get_all_films()
        return films


    def get_film_by_page_ref(self, page_ref, with_crew):

        if with_crew is True:
            film = FilmRepository.get_film_by_ref_with_crew(page_ref)
        else:
            film = FilmRepository.get_film_by_ref_without_crew(page_ref)

        return film


    def get_films_by_refs(self,page_refs, with_crew):

        if with_crew is True:
            films = self.repo.get_films_by_refs_with_crew(page_refs)
        else:
            films = self.repo.get_films_by_refs_without_crew(page_refs)
        return films


    def get_newest_film(self):

        film = self.repo.get_newest_film()
        return film


    def search_films(self, query: str):

        search_result = self.repo.search_films(query)
        return search_result


    async def create_multiple_films(self, film_tuples):
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

        inserted_films = self.repo.insert(film_data)


        # TODO removed last entry update add to logic to worker

        return inserted_films


    async def update_film(self, page_ref: str, timestamp=False):
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

            # TODO remove collector logic
            collector = FilmDetailCollector(page_ref)
            await collector.fetch_page()
            await collector.extract_details()

            print("Extracted description:", collector.description)

            # Map the collected details into a dictionary
            updated_attributes = Film.map_film_detailed(collector)
            print("Mapped description:", updated_attributes.get('description'))

            updated_film = self.repo.update_film(page_ref, updated_attributes)

            if not updated_film:
                return None
            # If timestamp flag is False, update related entities
            # Using the same session as the updated film
            if not timestamp:
                if updated_attributes.get('genres'):
                    self.genre_service.update_film_genres(updated_attributes['genres'])

                if updated_attributes.get('languages'):
                    self.lang_service.bulk_update_film_languages(updated_attributes['languages'])

                full_credits = []
                if updated_attributes.get('crew'):
                    full_credits.extend(updated_attributes['crew'])
                if updated_attributes.get('cast'):
                    full_credits.extend(updated_attributes['cast'])

                if full_credits:
                    self.crew_service.add_film_credits_bulk(
                        film_ref=updated_film.page_ref,
                        crew_data=full_credits
                    )

            return updated_film

        except Exception as e:
            db.session.rollback()
            print(f"Error updating film {page_ref}: {str(e)}")
            traceback.print_exc()
            return None

    async def update_multiple_films(self, film_refs: list[str], timestamp=False):
        # Step 1: Get only valid film_refs from the DB
        existing_refs = set(
            r[0] for r in db.session.query(Film.page_ref).filter(Film.page_ref.in_(film_refs)).all()
        )

        valid_refs = [ref for ref in film_refs if ref in existing_refs]
        if not valid_refs:
            print("No valid film references found.")
            return []

        # TODO remove from here
        collectors = await asyncio.gather(
            *[FilmService._fetch_and_extract(self, ref, 50) for ref in valid_refs],
            return_exceptions=False
        )

        updated_films_data = []
        for collector in collectors:
            updated_attributes = Film.map_film_detailed(collector)
            updated_attributes["page_ref"] = collector.ref
            updated_films_data.append(updated_attributes)


        self.repo.bulk_update_films(updated_films_data)

        # Process associated tables
        all_genres = []
        all_languages = []
        all_credits = []

        for collector in collectors:
            if collector.genre:
                all_genres.append((collector.ref, collector.genre))

            if collector.languages:
                all_languages.append((collector.ref, collector.languages))

            full_credits = []
            full_credits.extend(collector.crew.values())
            full_credits.extend(collector.cast.values())

            if full_credits:
                all_credits.append((collector.ref, full_credits))

        if all_genres:
            self.genre_service.update_film_genres(all_genres)
        if all_languages:
            self.lang_service.bulk_update_film_languages(all_languages)
        if all_credits:
            self.crew_service.add_film_credits_bulk(all_credits)

        return valid_refs


    async def update_multiple_films_redux(self,film_refs: list[str]):
        """
        Update multiple films using a shared HTTP session.
        """
        await FilmDetailCollector.enable_shared_session()
        try:
            for film_ref in film_refs:
                await self.update_film(film_ref)
        finally:
            await FilmDetailCollector.disable_shared_session()



    def get_films_by_crew_member(self, crew_ref: str):
        # Fetch the credits associated with the crew member
        film_credits = self.crew_service.get_credits_by_crew_ref(crew_ref)

        # Extract film ids and roles
        film_ids = [credit.film_id for credit in film_credits]
        roles = {credit.film_id: [] for credit in film_credits}

        # Map each film_id to its corresponding roles
        for credit in film_credits:
            roles[credit.film_id].append(credit.role.role)

        # Fetch films by their ids
        films = self.repo.get_films_by_refs_without_crew(film_ids)

        for film in films:
            film.roles = roles.get(film.page_ref, [])

        film_proxies = []

        for film in films:
            film_proxy = self.get_image_proxies(film)
            film_proxies.append(film_proxy)

        return film_proxies


    def get_image_proxies(self, film: Film):

        if film.image_ref:
            film.image_ref = ImageProxy.get_proxified_url(film.image_ref)
        if film.image_ref_large:
            film.image_ref_large = ImageProxy.get_proxified_url(film.image_ref_large)
        if film.banner_ref:
            film.banner_ref = ImageProxy.get_proxified_url(film.banner_ref)

        return film

    def update_column_for_films(self, column_name, column_value, film_page_refs):
        """Updates a given column (e.g., 'series_id') for a list of films (based on their page_ref)."""
        if not film_page_refs:

            return

        # Step 1: Prepare data for upsert (using page_ref and the dynamic column to update)
        data = [
            {"page_ref": film_ref, column_name: column_value}
            for film_ref in film_page_refs
        ]

        self.repo.upsert(
            data,
            cls_table=Film,
            conflict_columns=["page_ref"],  # Conflict on the `page_ref` column
            update_columns=[column_name]  # Dynamic column to update (e.g., `series_id`)
        )

        print(f"Successfully updated {len(film_page_refs)} films' {column_name}.")

    async def _fetch_and_extract(self, film_ref: str, sem):

        async with asyncio.Semaphore(sem):
            try:
                collector = FilmDetailCollector(film_ref)
                await collector.fetch_page()
                await collector.extract_details()
                return collector
            except Exception as e:
                print(f"[ERROR] Failed to collect for {film_ref}: {e}")
                return None


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        asyncio.run(FilmService.update_film('boogie-nights'))
