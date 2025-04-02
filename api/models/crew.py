from api import db


class Crew(db.Model):
    __tablename__ = 'crew'

    page_ref = db.Column(db.String(200), primary_key=True, nullable=False)  # Crew unique identifier
    name = db.Column(db.String(500))  # Name of the crew member

    # Relationship with credits (many-to-many through Credit table)
    credits = db.relationship('Credit', back_populates='crew', lazy='joined')

    def __repr__(self):
        return f'<Crew {self.name}>'
