from typing import List

from sqlalchemy import func, select, desc, distinct, true, asc
from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import Crew, Role
from ..models import Credit
from ..models import Film
from ..models import Film_Language, Language
from ..models import film_genre, Genre
from ..models import Film_Tag, Tag
from ..models import Film_Theme, Theme
from ..repositories.utils.bulk_persisting import BulkPersistence


class FilmRepository(BulkPersistence):

    def __init__(self):
        super().__init__()
        self.cls_table = Film
        self.conflict_columns = ['page_ref']
        self.update_columns = [
            'title',
            'title_original',
            'description',
            'image_ref',
            'image_ref_large',
            'banner_ref',
            'release_year',
            'runtime',
            'total_watches',
            'last_update',
            'series_id',
            'imdb_ref',
            'avg_rating'
        ]
    # CRUD
    def get_all_films(self):

        try:
            return Film.query.filter().all()
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []

    def get_newest_film(self):

        result = Film.query.order_by(Film.last_update.desc(), Film.id.desc()).first()
        return result

    def get_film_by_ref(self, page_ref):

        result = Film.query.filter_by(page_ref=page_ref).first()

        return result

    def get_films_by_refs(self, page_refs):

        if not page_refs:
            return []
        films = Film.query.filter(Film.page_ref.in_(page_refs)).order_by(desc(Film.total_watches)).all()
        return films

    def search_films(self, query: str, limit: int = 15):
        try:
            films_query = (
                db.session.query(Film)
                .filter(Film.title.ilike(f"%{query}%"))  # Filter films by title
                .order_by(
                    func.lower(Film.title).like(f"{query.lower()}%").desc(),  # Prioritize the exact match
                    desc(Film.total_watches)
                )
                .limit(limit)
            )
            films = films_query.all()
            return films

        except Exception as e:
            print(f"Error in search_films2: {e}")
            return []

    def get_all_film_meta_data(self, crew_role="director"):

        stmt = (
            select(
                Film.page_ref,
                Film.title,
                Film.release_year,
                Film.series_id,
                func.array_agg(func.distinct(Genre.genre)).label("genres"),
                func.array_agg(distinct(Language.language)).label("languages"),
                func.array_agg(distinct(Theme.theme_ref)).label("themes"),
                func.array_agg(distinct(Tag.tag_ref)).label("tags"),

                func.array_agg(func.distinct(Crew.page_ref)).label("crew_refs"),
            )
            .outerjoin(Credit, Credit.film_id == Film.page_ref)
            .outerjoin(Role, Role.id == Credit.role_id)
            .outerjoin(Crew, Crew.page_ref == Credit.crew_id)
            .outerjoin(Film_Language, Film.page_ref == Film_Language.c.film_id)
            .outerjoin(Language, Language.id == Film_Language.c.language_id)
            .outerjoin(film_genre, Film.page_ref == film_genre.c.film_id)
            .outerjoin(Genre, Genre.id == film_genre.c.genre_id)
            .outerjoin(Film_Tag, Film.page_ref == Film_Tag.c.film_id)  # if film_tag may be empty
            .outerjoin(Tag, Tag.id == Film_Tag.c.tag_id)
            .outerjoin(Film_Theme, Film.page_ref == Film_Theme.c.film_id)  # if you have a theme association table
            .outerjoin(Theme, Theme.id == Film_Theme.c.theme_id)
            .where(Film_Language.c.is_primary.is_(True))
            .where(Role.role == crew_role)
            .group_by(Film.page_ref, Film.title, Film.release_year)
        )

        return db.session.execute(stmt).mappings().all()

    def get_similar_films(self, page_ref: str, limit: int = 5, metric: str = "cosine") -> List[Film]:

        try:

            if metric == "cosine":
                op_str = "<=>"
            elif metric == "l2":
                op_str = "<->"
            elif metric in ("ip", "inner", "inner_product"):
                op_str = "<#>"
            else:
                raise ValueError("metric must be 'cosine', 'l2' or 'ip'")

            # subquery: hent embedding for kildens page_ref (som en enkelt kolonne)
            subq = db.session.query(Film.embedding.label("q_embedding")).filter(Film.page_ref == page_ref).subquery()

            # hovedquery: cross-join mod subquery, sørg for at både kilde- og mål-embedding ikke er NULL
            q = (
                db.session.query(Film)
                .join(subq, true())  # cross join -> én SQL-forespørgsel med subquery
                .filter(
                    subq.c.q_embedding.isnot(None),  # kilde har embedding
                    Film.embedding.isnot(None),  # mål har embedding
                    Film.page_ref != page_ref  # ekskluder kilden
                )
                .order_by(Film.embedding.op(op_str)(subq.c.q_embedding))
                .limit(limit)
            )

            return q.all()
        except SQLAlchemyError as e:
            print(f"Database error on find_similar: {e}")
            return []
        except Exception as e:
            print(f"Error in find_similar: {e}")
            return []

    def clear_column(self, column: str) -> bool:

        try:
            if isinstance(column, str):
                col_attr = getattr(Film, column)
            else:
                col_attr = column

            Film.query.update({col_attr: None}, synchronize_session=False)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error while clearing column {getattr(col_attr, 'key', str(column))}: {e}")
            return False

    def get_series(self, series_id):
        try:
            films = (
                db.session.query(Film)
                .filter(Film.series_id == series_id)
                .order_by(asc(Film.release_year))
                .all()
            )
            return films
        except Exception:
            db.session.rollback()
            raise

