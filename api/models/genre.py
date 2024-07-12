from api import db

film_genre_association = db.Table('genre_film',
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('film_id', db.Integer, db.ForeignKey('film.id'), primary_key=True)
)


class Genre(db.Model):
    __tablename__ = 'genre'

    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(80), unique=True, nullable=False)
    films = db.relationship('Film', secondary=film_genre_association, back_populates='genres')

    def to_dict(self):
        return {
            'id': self.id,
            'genre': self.title
        }

