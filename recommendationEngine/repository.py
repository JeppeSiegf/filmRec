
from .tables import Film, Genre, Credit, Role, Film_Language, Language, Film_genre, Film_Tag, Crew, Tag, Theme, \
    Film_Theme, Rating
from sqlalchemy import or_, Update, Insert
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, select, distinct, update

def update_embaddings(session, data, conflict_columns=None, update_columns=None):

    if not data:
        print("No data provided.")
        return []

    table = Film

    # default conflict / update behavior if not provided
    if conflict_columns is None:
        conflict_columns = ["page_ref"]
    if update_columns is None:
        update_columns = ["embedding"]

    stmt = insert(table).values(data)

    set_values = {col: stmt.excluded[col] for col in update_columns}
    conditions = [table.c[col].is_distinct_from(stmt.excluded[col]) for col in update_columns]

    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_=set_values,
        where=or_(*conditions) if conditions else None
    )

    try:
        session.execute(stmt)
        session.commit()
        print(f"Upserted {len(data)} entries.")
        return data
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error during bulk upsert: {e}")
        return []


def get_all_film_meta_data(session, crew_role="director"):

    stmt = (
        select(
            Film.c.page_ref.label("page_ref"),
            Film.c.title.label("title"),
            Film.c.release_year.label("release_year"),
            Film.c.series_id.label("series_id"),
            func.array_agg(func.distinct(Genre.c.genre)).label("genres"),
            func.array_agg(distinct(Language.c.language)).label("languages"),
            func.array_agg(distinct(Theme.c.theme_ref)).label("themes"),
            func.array_agg(distinct(Tag.c.tag_ref)).label("tags"),
            func.array_agg(func.distinct(Crew.c.page_ref)).label("crew_refs"),
        )
        .outerjoin(Credit, Credit.c.film_id == Film.c.page_ref)
        .outerjoin(Role, Role.c.id == Credit.c.role_id)
        .outerjoin(Crew, Crew.c.page_ref == Credit.c.crew_id)
        .outerjoin(Film_Language, Film.c.page_ref == Film_Language.c.film_id)
        .outerjoin(Language, Language.c.id == Film_Language.c.language_id)
        .outerjoin(Film_genre, Film.c.page_ref == Film_genre.c.film_id)
        .outerjoin(Genre, Genre.c.id == Film_genre.c.genre_id)
        .outerjoin(Film_Tag, Film.c.page_ref == Film_Tag.c.film_id)
        .outerjoin(Tag, Tag.c.id == Film_Tag.c.tag_id)
        .outerjoin(Film_Theme, Film.c.page_ref == Film_Theme.c.film_id)
        .outerjoin(Theme, Theme.c.id == Film_Theme.c.theme_id)
        .where(Film_Language.c.is_primary.is_(True))
        .where(Role.c.role == crew_role)
        .group_by(Film.c.page_ref, Film.c.title, Film.c.release_year)
    )

    result = session.execute(stmt).mappings().all()
    return result


def get_all_ratings(session):
    stmt = select(Rating)
    rows = session.execute(stmt).mappings().all()
    return rows


def clear_column(session, column: str) -> bool:

    try:

        # Table object: use .c to get column
        col_attr = Film.c[column] if isinstance(column, str) else column

        # Construct update statement
        stmt = update(Film).values({col_attr: None})

        # Execute and commit
        session.execute(stmt)
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error while clearing column {column}: {e}")
        return False

