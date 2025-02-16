from datetime import datetime
from api import db

class Film(db.Model):
    __tablename__ = 'film'

    page_ref = db.Column(db.String(250), primary_key=True, nullable=False)  # Primary key - Film slug used on source site
    image_ref = db.Column(db.String(250))  # Film poster reference
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)  # Auto-incrementing primary key  # Auto-incrementing ID using PostgreSQL sequence
    title = db.Column(db.String(500))  # Film title
    total_watches = db.Column(db.Integer)  # Total watches count
    last_update = db.Column(db.Date)  # Last update date
    release_year = db.Column(db.Integer)  # Year of release
    image_ref_large = db.Column(db.String(250)) # Higher quality film poster reference

    # Foreign Keys - Many to many
    genres = db.relationship('Genre', secondary='film_genre', backref=db.backref('films', lazy='dynamic'))
    credits = db.relationship('Credit', back_populates='film')

    from api.models.credit import Credit

    def __repr__(self):
        return f'<Film {self.title} ({self.release_year}) (page_ref={self.page_ref})>'
