from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_restx import Api  # Update to flask_restx
from config import Config

db = SQLAlchemy()
api = Api(
    title='My Title',
    version='1.0',
    description='A description',
    # All API metadata
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    api.init_app(app)

    with app.app_context():
        # Import and register your namespaces
        from api.controllers.genre_controller import api as genre_ns
        from api.controllers.film_controller import api as film_ns
        from api.controllers.user_controller import api as user_ns

        api.add_namespace(genre_ns, path='/api/genres')
        api.add_namespace(film_ns, path='/api/films')
        api.add_namespace(user_ns, path='/api/users')

        # Create tables
        db.create_all()

    return app
