from datetime import datetime
from api import db




class Film(db.Model):
    __tablename__ = 'film'

    # Reflecting the exact schema provided
    page_ref = db.Column(db.String(250), primary_key=True, nullable=False)  # Primary key - Film slug used on source site
    image_ref = db.Column(db.String(250))  # Optional image reference- wip
    id = db.Column(db.Integer, default=db.func.nextval('id_seq'), nullable=False)  # Auto-incrementing ID using PostgreSQL sequence
    title = db.Column(db.String(500))  # Film title
    total_watches = db.Column(db.Integer)  # Total watches count
    last_update = db.Column(db.Date, nullable=False)  # Last update date
    release_year = db.Column(db.Integer)  # Year of release

    # Relationship example if required
    genres = db.relationship('Genre', secondary='film_genre', backref=db.backref('films', lazy='dynamic'))


    def __repr__(self):
        return f'<Film {self.title} ({self.release_year}) (page_ref={self.page_ref})>'
