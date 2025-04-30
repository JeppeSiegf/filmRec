from api.repositories.series_repository import SeriesRepository
from api.services.film_service import FilmService


class SeriesService:

    def __init__(self):
        self.repo = SeriesRepository()
        self.film_service = FilmService()


    async def upsertFilmSeries(self,series: list[tuple]) -> None:

        all_film_refs = []
        for col in series:
            _, _, _, film_refs = col
            all_film_refs.extend(film_refs)

        # Get valid films from DB
        valid_films = self.film_service.get_films_by_refs(all_film_refs, False)
        valid_refs = {film.page_ref for film in valid_films}

        # Load all existing series from DB
        existing_series = {s.page_ref: s for s in self.repo.get_all()}

        upsert_series_data = []

        # Step 4: Determine which series need upsert
        for page_ref, name, expected_count, film_refs in series:
            cleaned_refs = list(set(film_refs) & valid_refs)
            if len(cleaned_refs) < 2:
                continue  # Skip collections with fewer than 2 valid films

            existing = existing_series.get(page_ref)
            db_film_count = len(existing.films.all()) if existing else 0

            if not existing or db_film_count != expected_count:
                upsert_series_data.append({"page_ref": page_ref, "name": name, "film_refs": cleaned_refs})

        # Bulk upsert the series and get film update map
        film_update_map = self.repo.bulk_upsert(upsert_series_data)

        # Update film relationships per series
        for series_ref, film_refs in film_update_map.items():
            series = self.repo.get_by_ref(series_ref)
            self.film_service.update_series_id(series, film_refs)
