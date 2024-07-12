from datetime import datetime
from api import db
from api.models.genre import film_genre_association


# app/models/film.py
film_genre = db.Table(
    'film_genre',
    db.Column('film_id', db.Integer, db.ForeignKey('film.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True)
)

class Film(db.Model):

    __tablename__ = 'film'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)
    total_watches = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.Date, nullable=False)
    page_ref = db.Column(db.String(500), nullable=False)
    img_ref = db.Column(db.String(500), nullable=False)

    genres = db.relationship('Genre', secondary=film_genre, backref=db.backref('related_films', lazy='dynamic'))
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'release_year': self.year,
            'total_watches': self.total_watches,
            'last_updated': self.last_updated.isoformat(),
            'ref': self.ref,
            'img_reg': self.img_reg,
            'genres': [genre.to_dict() for genre in self.genres]
        }