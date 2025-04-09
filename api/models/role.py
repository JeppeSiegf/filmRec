from api import db


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)  # Primary key (auto-increment)
    role = db.Column(db.String(100), nullable=False,  unique=True)  # Role description (e.g., Director)

    # Relationship with credits (many-to-many through Credit table)
    credits = db.relationship('Credit', back_populates='role')
