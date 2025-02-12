from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased, joinedload
from datetime import datetime
from sqlalchemy import desc

from api import db
from api.models.film import Film
from api.models.genre import Genre
from api.models.credit import Credit


class FilmRepository:
    # CRUD
    @staticmethod
    def get_all_films():
        try:
            return Film.query.all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_film_by_ref(page_ref):
        try:
            film = (Film.query.filter_by(page_ref=page_ref)
                    .options(
                joinedload(Film.genres),
                joinedload(Film.credits).joinedload(Credit.crew),
                joinedload(Film.credits).joinedload(Credit.role)
            )
                    .first()
                    )
            if not film:
                return None

                # Extract director names (list format)
            film.directors = [c.crew.name for c in film.credits if c.role and c.role.role == 'director']

            return film

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def search_films(query: str):
        try:
            films_query = Film.query.filter(Film.title.ilike(f"%{query}%"))
            films_query = films_query.order_by(desc(getattr(Film, 'total_watches')))
            return films_query.limit(10).all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def create_film(film):


        FilmRepository._validate_film(film)

        try:

            db.session.add(film)
            db.session.commit()
            return film
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None

    @staticmethod
    def update_film(film, updates):
        if film is None:
            return None
        for key, value in updates.items():
            setattr(film, key, value)
        try:
            db.session.commit()
            return film

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return None

    @staticmethod
    def delete_film(page_ref):
        try:
            film = Film.query.filter_by(page_ref=page_ref).first()
            if film:
                db.session.delete(film)
                db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")

    @staticmethod
    def update_film_genres(existing_film, genres):

        try:

            existing_genres = {g.genre: g for g in Genre.query.filter(Genre.genre.in_(genres)).all()}
            new_genres = []

            for genre_title in genres:
                if genre_title in existing_genres:
                    new_genres.append(existing_genres[genre_title])
                else:
                    new_genre = Genre(genre=genre_title)
                    db.session.add(new_genre)
                    new_genres.append(new_genre)

            existing_film.genres = new_genres
            db.session.commit()
            return new_genres

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")

    @staticmethod
    def _validate_film(film):
        required_fields = ['title', 'page_ref', 'last_update']
        for field in required_fields:
            if getattr(film, field, None) is None:
                raise ValueError(f"Film is missing required field: {field}")
