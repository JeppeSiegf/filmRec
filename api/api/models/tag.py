from .. import db

Film_Tag = db.Table(
    'film_tag',
    db.Column('film_id', db.String(250), db.ForeignKey('film.page_ref'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True, unique=True),
)


class Tag(db.Model):
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True, default=db.func.nextval('tag_id_seq'))
    tag_ref = db.Column(db.String(250), nullable=False)
    tag_name = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'{self.tag_name}'
