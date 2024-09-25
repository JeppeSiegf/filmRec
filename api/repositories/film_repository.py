from datetime import datetime

from sqlalchemy import desc

from api.models.crew import Crew
from api.models.film import Film
from api.models.genre import Genre, film_genre
from api import db


def generate_page_ref(director_name):
    pass


class FilmRepository:

    # CRUD
    @staticmethod
    def get_all_films():
        return Film.query.all()

    @staticmethod
    def get_film_by_ref(page_ref):
        # Query by page_ref as this is the primary key now
        return Film.query.filter_by(page_ref=page_ref).first()

    @staticmethod
    def search_films(query: str):
        # Query to filter films based on title
        films_query = Film.query.filter(Film.title.ilike(f"%{query}%"))

        films_query = films_query.order_by(desc(getattr(Film, 'total_watches')))

        return films_query.limit(10).all()

    @staticmethod
    def create_film(film):
        # film should be an instance of the Film class
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")

        FilmRepository._validate_film(film)

        db.session.add(film)
        db.session.commit()
        return film

    @staticmethod
    def update_film(existing_film, updated_data):
        # Update the film's attributes
        if 'title' in updated_data:
            existing_film.title = updated_data['title']

        if 'image_ref' in updated_data:
            existing_film.image_ref = updated_data['image_ref']

        if 'total_watches' in updated_data:
            existing_film.total_watches = updated_data['total_watches']

        if 'release_year' in updated_data:
            existing_film.release_year = updated_data['release_year']

        # Update last update timestamp
        existing_film.last_update = datetime.now()

        # Commit changes to the database
        db.session.commit()
        return existing_film

    @staticmethod
    def delete_film(page_ref):
        # Query the film by page_ref
        film = Film.query.filter_by(page_ref=page_ref).first()
        if film:
            db.session.delete(film)
            db.session.commit()

    # Additional methods

    # Adds many-to-many relation to db  used both by update and create
    @staticmethod
    def update_film_genres(existing_film, genres):
        # Clear existing genres
        existing_film.genres.clear()

        # Add new genres
        for genre_title in genres:
            # Check if the genre already exists in the database
            genre = Genre.query.filter_by(genre=genre_title).first()

            # If the genre exists, add it to the film's genres
            if genre:
                existing_film.genres.append(genre)
            else:
                # Optionally: Create a new genre if it doesn't exist
                new_genre = Genre(genre=genre_title)
                db.session.add(new_genre)  # Add new genre to the session
                existing_film.genres.append(new_genre)  # Associate the new genre with the film

        # Commit changes to the database
        db.session.commit()


    # Validates non-nullable fields and title (might update schema)
    @staticmethod
    def _validate_film(film):
        required_fields = ['title', 'page_ref', 'last_update']

        for field in required_fields:
            if getattr(film, field, None) is None:
                raise ValueError(f"Film is missing required field: {field}")
