from api import db

film_genre = db.Table(
    'film_genre',
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('film_id', db.String(250), db.ForeignKey('film.page_ref'), primary_key=True)
)


class Genre(db.Model):
    __tablename__ = 'genre'

    id = db.Column(db.Integer, primary_key=True,
                   default=db.func.nextval('id_seq'))  # Primary key with PostgreSQL sequence
    genre = db.Column(db.String(255), nullable=True)  # Genre name

    def __repr__(self):
        return f'<{self.genre}>'
