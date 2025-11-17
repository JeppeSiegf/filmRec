from .. import db


Film_Theme = db.Table(
    'film_theme',
    db.Column('film_id', db.String(250), db.ForeignKey('film.page_ref'), primary_key=True),
    db.Column('theme_id', db.Integer, db.ForeignKey('theme.id'), primary_key=True),
)


class Theme(db.Model):
    __tablename__ = 'theme'

    id = db.Column(db.Integer, primary_key=True, default=db.func.nextval('theme_id_seq'))
    theme_ref = db.Column(db.String(250), nullable=False)
    theme_name = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<{self.theme_name}>'
