from api import db

class Rating(db.Model):

    __tablename__ = 'user_rating'

    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    rating = db.Column(db.Integer)
    liked = db.Column(db.Boolean)
    when_logged = db.Column(db.Date, nullable=False)

    film = db.relationship('Film', backref=db.backref('user_ratings', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('user_ratings', cascade='all, delete-orphan'))


def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'liked': self.like,
            'film_id': self.film_id,
            'user_id': self.user_id
        }