from api.models.film import Film
from api.models.genre import Genre
from api import db


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
        return Film.query.filter(Film.title.ilike(f"%{query}%")).limit(10).all()

    @staticmethod
    def create_film(film):
        # film should be an instance of the Film class
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")

        FilmRepository._validate_film(film)

        # Handle genre associations
        if film.genres:
            FilmRepository.update_film_gerne(film)
        for genre_title in film.genres:
            genre = Genre.query.filter_by(genre=genre_title).first()  # `genre` field in Genre table
            if genre:
                film.genres.append(genre)  # Assuming `Film` has a many-to-many `genres` relationship

        db.session.add(film)
        db.session.commit()
        return film

    @staticmethod
    def update_film(film):
        # film should be an instance of the Film class with updated attributes
        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")



        existing_film = Film.query.filter_by(page_ref=film.page_ref).first()

        if not existing_film:
            return None  # Return if the film with the given page_ref is not found

        # Update attributes
        existing_film.title = film.title
        existing_film.release_year = film.release_year
        existing_film.total_watches = film.total_watches
        existing_film.image_ref = film.image_ref

        # Update genres
        if film.genres is not None:
            FilmRepository._update_film_genres( film, existing_film)

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
    def _update_film_genres( film, existing_film=None):

        if not isinstance(film, Film):
            raise TypeError("Expected a Film instance.")

        # Use existing_film if provided, otherwise the film itself
        target_film = existing_film if existing_film else film

        if film.genres:
            # Clear existing genres if updating
            if existing_film:
                target_film.genres = []
            for genre_title in film.genres:
                genre = Genre.query.filter_by(genre=genre_title).first()  # `genre` field in Genre table
                if genre:
                    target_film.genres.append(genre)  # Assuming `Film` has a many-to-many `genres` relationship

    # Validates non-nullable fields and title (might update schema)

    @staticmethod
    def _validate_film(film):
        required_fields = ['title', 'page_ref', 'last_update']

        for field in required_fields:
            if getattr(film, field, None) is None:
                raise ValueError(f"Film is missing required field: {field}")


