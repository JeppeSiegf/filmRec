from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from config import Config

db = SQLAlchemy()
api = Api(
    title='My Title',
    version='1.2',
    description='A description',
    # All API metadata
)


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    api.init_app(app)

    with app.app_context():
        from api.models import Film, Credit, Genre, Crew, Role

        # Import and register your namespaces
        from api.controllers.genre_controller import api as genre_ns
        from api.controllers.film_controller import api as film_ns
        from api.controllers.user_controller import api as user_ns
        # from api.controllers.film_rec_controller import api as rec_ns

        api.add_namespace(genre_ns, path='/api/genres')
        api.add_namespace(film_ns, path='/api/films')
        api.add_namespace(user_ns, path='/api/users')
        # api.add_namespace(rec_ns, path='/api/recommendation')
    return app


def create_db(app):
    with app.app_context():
        db.create_all()

