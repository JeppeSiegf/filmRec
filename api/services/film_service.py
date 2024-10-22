
from datetime import datetime, timedelta
from api.dataCollectors.film_detail_collector import FilmDetailCollector
from api.models.film import Film
from api.repositories.film_repository import FilmRepository
from api.services.crew_service import CrewService


class FilmService:

    @staticmethod
    def get_all_films():
        films = FilmRepository.get_all_films()
        # Append directors to each film
        for film in films:
            film.directors = CrewService.get_film_director(film.page_ref)  # Assuming page_ref is unique
        return films

    @staticmethod
    def get_film_by_page_ref(page_ref):
        film = FilmRepository.get_film_by_ref(page_ref)
        if film:
            film.directors = CrewService.get_film_director(film.page_ref)  # Get directors for this specific film
        return film

    @staticmethod
    def search_films(query: str):
        search_result = FilmRepository.search_films(query)
        for film in search_result:
            # print(film.title)
            # asyncio.run(FilmService.update_film(film.page_ref))
            film.directors = CrewService.get_film_director(film.page_ref)

        return search_result

    @staticmethod
    def get_films_recs(top_films, limit=10):

        return FilmRepository.get_films_recs(top_films, limit)

    @staticmethod
    def create_film(film: Film):
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")

        existing_film = FilmRepository.get_film_by_ref(film.page_ref)

        if existing_film:
            raise ValueError(f'{film.title} already exists.')

        return FilmRepository.create_film(film)

    @staticmethod
    async def update_film(page_ref):
        # Step 1: Retrieve the existing film
        print('trigger')
        existing_film = FilmRepository.get_film_by_ref(page_ref)

        if not existing_film:
            print('not in db')
            return None  # Raise an exception if the film does not exist

        needs_update = False
        needs_update = any(
            getattr(existing_film, attr) in (None, 0)
            for attr in ['title', 'image_ref', 'total_watches', 'release_year', 'genres']
        )

        film_service_instance = FilmService()
        #if film_service_instance.__is_time_to_update(existing_film.last_update, 30):
        #  print('date')
        #    needs_update = True


        if not needs_update:
            print('no need for update')
            return existing_film  # No need to update

        updated_info = FilmDetailCollector(page_ref)
        await updated_info.fetch_page_dom()  # Await the asynchronous call
        await updated_info.fetch_page_script(updated_info.dom)  # Await the asynchronous call
        await updated_info.extract_details()  # Await the asynchronous call

        updated_data = {
            'title': updated_info.title,  # Assuming title is fetched in extract_details
            'image_ref': updated_info.image_ref,
            'total_watches': updated_info.total_watches,
            'release_year': updated_info.release_year,
            'genres': updated_info.genre,  # Assuming genres are already in the correct format
            'directors': updated_info.director,

        }
        print(updated_data)
        # Step 2: Update the film's attributes

        FilmRepository.update_film(existing_film, updated_data)

        # Step 3: Update the genres if provided
        if 'genres' in updated_data:
            FilmRepository.update_film_genres(existing_film, updated_data['genres'])

        if 'directors' in updated_data and updated_data['directors']:

            for director_ref, director_name in updated_data['directors'].items():
                CrewService.add_director_credit(existing_film.page_ref, director_name, director_ref)

        return existing_film  # Return the updated film object

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


