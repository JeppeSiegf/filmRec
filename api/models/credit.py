from api import db


class Credit(db.Model):
    __tablename__ = 'credit'

    credit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key
    film_id = db.Column(db.String(250), db.ForeignKey('film.page_ref'), nullable=False)  # Foreign key to Film
    crew_id = db.Column(db.String(200), db.ForeignKey('crew.page_ref'), nullable=False)  # Foreign key to Crew
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    rank = db.Column(db.Integer)


    # Relationships
    film = db.relationship('Film', back_populates='credits', lazy='joined')
    crew = db.relationship('Crew', back_populates='credits', lazy='joined')
    role = db.relationship('Role', back_populates='credits', lazy='joined')

    def __repr__(self):
        return f'<Credit {self.film.title} - {self.crew.name} as {self.role.role}>'
