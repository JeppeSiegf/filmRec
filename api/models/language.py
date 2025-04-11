from api import db

Film_Language = db.Table(
    'film_language',
    db.Column('film_id', db.String(250), db.ForeignKey('film.page_ref'), primary_key=True),
    db.Column('language_id', db.Integer, db.ForeignKey('language.id'), primary_key=True, unique=True),
    db.Column('is_primary', db.Boolean, nullable=False, )
)


class Language(db.Model):
    __tablename__ = 'language'

    id = db.Column(db.Integer, primary_key=True, default=db.func.nextval('language_id_seq'))
    language = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return f'<{self.language}>'
