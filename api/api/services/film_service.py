import asyncio

from .. import create_app
# from dataCollectors.film_detail_collector import FilmDetailCollector
from ..models import Credit, Film
from ..repositories.film_repository import FilmRepository
from ..services.crew_service import CrewService
from ..services.genre_service import GenreService
from ..services.imdb_service import IMDBService
from ..services.language_service import LanguageService
from ..services.series_service import SeriesService


class FilmService:

    def __init__(self):
        self.repo = FilmRepository()
        self.genre_service = GenreService()
        self.lang_service = LanguageService()
        self.crew_service = CrewService()
        self.series_service = SeriesService()

        self.count = 0
        # TODO use
        self.image_attrs = ['image_ref','image_ref_large','banner_ref']

    def get_all_films(self):

        all_films = self.repo.get_all_films()

        return all_films

    def get_film_by_page_ref(self, page_ref, imdb_info = False):

        film = self.repo.get_film_by_ref(page_ref)
        film.crew_members = [self.serialize_credit(c) for c in film.credits if c.rank is not None]

        if film.imdb_ref is not None and imdb_info is True:
            film.imdb_rating = IMDBService().get_rating(film.imdb_ref)

        return film

    def get_films_by_refs(self, page_refs):

        films = self.repo.get_films_by_refs(page_refs)

        return films

    def get_newest_film(self):

        film = self.repo.get_newest_film()
        return film

    def search_films(self, query: str):

        search_result = self.repo.search_films(query)
        return search_result

    def get_meta_data(self):

        metadata = self.repo.get_all_film_meta_data()
        return metadata

    def create_multiple_films(self, film_data_list):
        """Create multiple films from JSON format data."""

        if not isinstance(film_data_list, list):
            raise TypeError("Expected a list of dictionaries.")

        # Filter out any None or invalid entries
        valid_film_data = [film for film in film_data_list if film is not None and isinstance(film, dict)]

        if not valid_film_data:
            print("No valid films to insert.")
            return []

        processed_films = []
        for film_data in valid_film_data:
            if 'page_ref' in film_data and 'title' in film_data:
                processed_films.append(film_data)
            else:
                print(f"Skipping film data missing required fields: {film_data}")

        if not processed_films:
            print("No films with required fields found.")
            return []

        inserted_films = self.repo.insert(processed_films)

        # TODO removed last entry update add to logic to worker

        return inserted_films

    async def scrape_multiple_films(self, film_refs: list[str]) -> list:
        """Scrape film data from external sources."""
        # TODO remove from here when worker is done
        await FilmDetailCollector.enable_shared_session()
        sem = asyncio.Semaphore(50)

        tasks = [
            self._fetch_and_extract(ref, sem)
            for ref in film_refs
        ]
        collectors = await asyncio.gather(
            *tasks,
            return_exceptions=False
        )
        await FilmDetailCollector.disable_shared_session()

        return collectors

    def update_multiple_films(self, films : list):
        """Validate scraped data and update database."""
        if not films:
            print("No collectors provided.")
            return []

        # Get existing refs for validation
        film_refs = [film['page_ref'] for film in films]
        existing_refs = set(
            r.page_ref for r in self.repo.get_films_by_refs(film_refs)
        )

        # Filter to only valid collectors
        valid_film = [
            film for film in films
            if film['page_ref'] in existing_refs
        ]

        if not films:
            print("No valid film references found.")
            return []

        updated_films_data = []
        allowed_columns = {
            'page_ref', 'title', 'title_original', 'description',
            'image_ref', 'image_ref_large', 'banner_ref', 'release_year',
            'runtime', 'total_watches', 'last_update', 'imdb_ref', 'avg_rating', 'series_id'
        }

        series_map = {s.page_ref: s.id for s in self.series_service.get_all()}

        for film in valid_film:
            film_data = film
            cleaned_attributes = {k: v for k, v in film_data.items() if k in allowed_columns}

            # Map series_id from page_ref to actual id
            if cleaned_attributes.get("series_id"):
                cleaned_attributes["series_id"] = series_map.get(cleaned_attributes["series_id"], None)

            updated_films_data.append(cleaned_attributes)

        self.repo.upsert(updated_films_data)

        # Process associated tables
        all_genres = []
        all_languages = []
        all_credits = []

        for film in valid_film:
            film_data = film

            if film_data.get('genres'):
                all_genres.append((film_data['page_ref'], film_data['genres']))

            if film_data.get('languages'):
                all_languages.append((film_data['page_ref'], film_data['languages']))

            full_credits = []
            if film_data.get('crew'):
                full_credits.extend(film_data['crew'])
            if film_data.get('cast'):
                full_credits.extend(film_data['cast'])

            if full_credits:
                all_credits.append((film_data['page_ref'], full_credits))

        if all_genres:
            self.genre_service.update_film_genres(all_genres)
        if all_languages:
            self.lang_service.bulk_update_film_languages(all_languages)
        if all_credits:
            self.crew_service.add_film_credits_bulk(all_credits)

        return [film['page_ref'] for film in valid_film]

    def get_films_by_crew_member(self, crew_ref: str):
        # Fetch the credits associated with the crew member
        film_credits = self.crew_service.get_credits_by_crew_ref(crew_ref)

        # Extract film ids and build roles mapping in one pass
        film_ids = []
        roles = {}

        for credit in film_credits:
            if credit.film_id not in roles:
                film_ids.append(credit.film_id)
                roles[credit.film_id] = []

            if credit.rank is not None:
                roles[credit.film_id].append(credit.role.role)

        # Fetch films and assign roles
        films = self.repo.get_films_by_refs(film_ids)
        for film in films:
            film.roles = roles.get(film.page_ref, [])

        return films



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

    # async def _fetch_and_extract(
    #         self,
    #         film_ref: str,
    #         sem: asyncio.Semaphore
    # ) -> FilmDetailCollector | None:
    #     # This async with uses the shared semaphore
    #     async with sem:
    #
    #         try:
    #             collector = FilmDetailCollector(film_ref)
    #             await collector.fetch_page()
    #             await collector.extract_details()
    #             print(collector.data)
    #             print(self.count)
    #             self.count += 1
    #
    #             return collector.data
    #         except Exception as e:
    #             print(f"[ERROR] Failed to collect for {film_ref}: {e}")
    #             return None
    #
    #

    def serialize_credit(self, credit: Credit):

        return {
            "page_ref": credit.crew.page_ref,
            "name": credit.crew.name,
            "role": credit.role.role,
            "rank": credit.rank
        }

    def get_film_series(self, series_id):

        return self.repo.get_series(series_id)


if __name__ == "__main__":
    app = create_app()
    with app.app_context():

        service = FilmService()
        films = asyncio.run(service.scrape_multiple_films(film_refs=["se7en"]))
        service.update_multiple_films(films)





