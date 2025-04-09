
from api import db

class Series(db.Model):
    __tablename__ = 'series'

    id = db.Column(db.Integer, primary_key=True)  # Auto-increment primary key
    page_ref = db.Column(db.String(50), nullable=False, unique=True)  # Film series reference (must match DDL)
    name = db.Column(db.String(50), nullable=False)  # Series name

    films = db.relationship('Film', back_populates='series', lazy='dynamic')
