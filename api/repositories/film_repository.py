from api.models.film import Film
from api.models.genre import Genre
from api import db

class FilmRepository:

    @staticmethod
    def get_all_films():
        return Film.query.all()

    @staticmethod
    def get_film_by_id(film_id):
        return Film.query.get(film_id)

    @staticmethod
    def create_film(title, year, total_watches, ref, img_reg, genres):
        film = Film(title=title, year=year, total_watches=total_watches, ref=ref, img_reg=img_reg)
        for genre_title in genres:
            genre = Genre.query.filter_by(title=genre_title).first()
            if genre:
                film.genres.append(genre)
        db.session.add(film)
        db.session.commit()
        return film

    @staticmethod
    def update_film(film_id, title=None, year=None, total_watches=None, ref=None, img_reg=None, genres=None):
        film = Film.query.get(film_id)
        if title:
            film.title = title
        if year:
            film.year = year
        if total_watches is not None:
            film.total_watches = total_watches
        if ref:
            film.ref = ref
        if img_reg:
            film.img_reg = img_reg
        if genres is not None:
            film.genres = []
            for genre_title in genres:
                genre = Genre.query.filter_by(title=genre_title).first()
                if genre:
                    film.genres.append(genre)
        db.session.commit()
        return film

    @staticmethod
    def delete_film(film_id):
        film = Film.query.get(film_id)
        db.session.delete(film)
        db.session.commit()