from datetime import datetime

from sqlalchemy import Sequence
from pgvector.sqlalchemy import Vector

from .. import db


class Film(db.Model):
    __tablename__ = 'film'

    page_ref = db.Column(db.String(250), primary_key=True, nullable=False)
    id = db.Column(db.Integer, Sequence('id_seq'), nullable=False)

    # Film attributes
    title = db.Column(db.String(500))
    title_original = db.Column(db.String(500))
    description = db.Column(db.String(1000))
    image_ref = db.Column(db.String(250))
    image_ref_large = db.Column(db.String(250))
    banner_ref = db.Column(db.String(250))
    total_watches = db.Column(db.Integer)
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    release_year = db.Column(db.Integer)
    runtime = db.Column(db.Integer)
    imdb_ref = db.Column(db.String(10))
    avg_rating = db.Column(db.Float)

    embedding = db.Column(Vector(100))

    # Relationships
    genres = db.relationship('Genre', secondary='film_genre', backref=db.backref('films', lazy='dynamic'))
    languages = db.relationship('Language', secondary='film_language', backref=db.backref('films', lazy='dynamic'))
    themes = db.relationship('Theme', secondary='film_theme', backref=db.backref('films', lazy='dynamic'))
    tags = db.relationship('Tag', secondary='film_tag', backref=db.backref('films', lazy='dynamic'))

    credits = db.relationship('Credit', back_populates='film')

    series_id = db.Column(db.Integer, db.ForeignKey('series.id'))
    series = db.relationship('Series', back_populates='films')

    # For create
    @staticmethod
    def map_film_simple(film_tuple):

        if not isinstance(film_tuple, (list, tuple)):
            raise ValueError("Expected a tuple or list.")

        # Unpack values safely (default to None if missing)
        title = film_tuple[0] if len(film_tuple) > 0 else None
        page_ref = film_tuple[1] if len(film_tuple) > 1 else None
        release_year = film_tuple[2] if len(film_tuple) > 2 else None

        print(f"Extracted page_ref: {page_ref}")
        try:
            release_year = int(release_year)
        except (TypeError, ValueError):
            release_year = None

        return {
            'page_ref': page_ref,
            'title': title,
            'title_original': None,
            'description': None,
            'image_ref': None,
            'image_ref_large': None,
            'banner_ref': None,
            'release_year': release_year,
            'runtime': None,
            'total_watches': None,
            'last_update': datetime.utcnow(),
            'series_id': None,
            'imdb_ref': None,
            'avg_rating': None

        }

    # For updates, using a FilmDetailCollector instance.
    @staticmethod
    def map_film_detailed(film_detail):

        if not hasattr(film_detail, 'ref'):
            raise ValueError("Expected a FilmDetailCollector instance with attribute 'ref'.")

        return {
            'page_ref': film_detail.ref,
            'title': film_detail.title,
            'title_original': film_detail.title_original,
            'description': film_detail.description,
            'image_ref': film_detail.image_ref,
            'image_ref_large': film_detail.image_ref_large,
            'banner_ref': film_detail.banner_ref,
            'release_year': film_detail.release_year,
            'runtime': film_detail.runtime,
            'total_watches': film_detail.total_watches,
            'last_update': datetime.utcnow(),
            'genres': film_detail.genre,
            'languages': film_detail.languages,
            'series_id': film_detail.series,
            'crew': film_detail.crew,
            'cast': film_detail.cast,
            'imdb_ref': film_detail.imdb_ref,
            'avg_rating': film_detail.avg_rating

        }

    def __repr__(self):
        return f'<Film {self.title} ({self.release_year}) (page_ref={self.page_ref})>'
