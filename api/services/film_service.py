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

        self.count = 0
        # TODO use
        self.image_attrs = ['image_ref','image_ref_large','banner_ref']

    def get_all_films(self):

        films = self.repo.get_all_films()
        return films

    def get_film_by_page_ref(self, page_ref, with_crew, image_proxies):

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

    def create_multiple_films(self, film_tuples):

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

    async def update_multiple_films(self, film_refs: list[str], timestamp=False):

        existing_refs = set(
            r.page_ref for r in self.repo.get_films_by_refs_without_crew(film_refs)
        )

        film_refs = set(film_refs)

        valid_refs = [ref for ref in film_refs if ref in existing_refs]
        if not valid_refs:
            print("No valid film references found.")
            return []

        # TODO remove from here
        await FilmDetailCollector.enable_shared_session()
        sem = asyncio.Semaphore(100)

        tasks = [
            self._fetch_and_extract(ref, sem)
            for ref in valid_refs
        ]
        collectors = await asyncio.gather(
            *tasks,
            return_exceptions=False

        )
        await FilmDetailCollector.disable_shared_session()

        updated_films_data = []
        allowed_columns = {
            'page_ref', 'title', 'title_original', 'description',
            'image_ref', 'image_ref_large', 'banner_ref', 'release_year',
            'runtime', 'total_watches', 'last_update',
        }

        for collector in collectors:
            # Map the film details into a dictionary.
            updated_attributes = Film.map_film_detailed(collector)
            updated_attributes["page_ref"] = collector.ref

            # Remove keys that are not columns in the Film table (i.e. "crew" and "cast")
            cleaned_attributes = {k: v for k, v in updated_attributes.items() if k in allowed_columns}
            updated_films_data.append(cleaned_attributes)

        self.repo.upsert(updated_films_data)

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
            full_credits.extend(collector.crew)
            full_credits.extend(collector.cast)

            if full_credits:
                all_credits.append((collector.ref, full_credits))

        if all_genres:
            self.genre_service.update_film_genres(all_genres)
        if all_languages:
            self.lang_service.bulk_update_film_languages(all_languages)
        if all_credits:
            self.crew_service.add_film_credits_bulk(all_credits)

        return valid_refs

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

        return films


    def get_image_proxies(self, film: Film):

        if film.image_ref:
            film.image_ref = ImageProxy.get_proxified_url(film.image_ref)
        if film.image_ref_large:
            film.image_ref_large = ImageProxy.get_proxified_url(film.image_ref_large)
        if film.banner_ref:
            film.banner_ref = ImageProxy.get_proxified_url(film.banner_ref)

        return film

    def update_column_for_films(self, column_name, column_value, film_page_refs):

        if not film_page_refs:
            return

        data =[
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

    async def _fetch_and_extract(
            self,
            film_ref: str,
            sem: asyncio.Semaphore
    ) -> FilmDetailCollector | None:
        # This async with uses the shared semaphore
        async with sem:

            try:
                collector = FilmDetailCollector(film_ref)
                await collector.fetch_page()
                await collector.extract_details()
                print(collector.title)
                print(self.count)
                self.count += 1

                return collector
            except Exception as e:
                print(f"[ERROR] Failed to collect for {film_ref}: {e}")
                return None


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        service = FilmService()
        asyncio.run(service.update_multiple_films(['a-good-day-to-die-hard']))
