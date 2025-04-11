from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
api = Api()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    db.init_app(app)
    api.init_app(app)

    with app.app_context():
        from api.models import Film, Credit, Genre, Crew, Role, language, series

        # Import and register your namespaces
        from api.controllers.genre_controller import api as genre_ns
        from api.controllers.film_controller import api as film_ns
        from api.controllers.user_controller import api as user_ns
        from api.controllers.film_rec_controller import api as rec_ns
        from api.controllers.proxy_controller import api as proxy_ns
        from api.controllers.ingestion_controller import api as ingest_ns

        api.add_namespace(genre_ns, path='/api/genres')
        api.add_namespace(film_ns, path='/api/films')
        api.add_namespace(user_ns, path='/api/users')
        api.add_namespace(rec_ns, path='/api/recommendation')
        api.add_namespace(proxy_ns, path='/api/proxy')
        api.add_namespace(ingest_ns, path='/api/ingestion')
        # api.add_namespace(tasks_ns, path='/api/tasks')

    return app


def create_db(app):
    with app.app_context():
        db.create_all()
