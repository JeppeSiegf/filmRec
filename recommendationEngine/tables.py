# repository.py
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, ForeignKey, MetaData
from sqlalchemy.dialects.postgresql import ARRAY

metadata = MetaData()

# Main film table
Film = Table(
    'film', metadata,
    Column('page_ref', String, primary_key=True),
    Column('title', String),
    Column('release_year', Integer),
    Column('series_id', String),
    Column('embedding', ARRAY(Float)),
)

# Genre table + many-to-many association
Genre = Table(
    'genre', metadata,
    Column('id', Integer, primary_key=True),
    Column('genre', String),
)

Film_genre = Table(
    'film_genre', metadata,
    Column('film_id', String, ForeignKey('film.page_ref')),
    Column('genre_id', Integer, ForeignKey('genre.id')),
)

# Language table + association
Language = Table(
    'language', metadata,
    Column('id', Integer, primary_key=True),
    Column('language', String),
)

Film_Language = Table(
    'film_language', metadata,
    Column('film_id', String, ForeignKey('film.page_ref')),
    Column('language_id', Integer, ForeignKey('language.id')),
    Column('is_primary', Boolean),
)

# Crew / Credits
Crew = Table(
    'crew', metadata,
    Column('page_ref', String, primary_key=True),
    Column('name', String),
)

Role = Table(
    'role', metadata,
    Column('id', Integer, primary_key=True),
    Column('role', String),
)

Credit = Table(
    'credit', metadata,
    Column('credit_id', Integer, primary_key=True, autoincrement=True),
    Column('film_id', String, ForeignKey('film.page_ref')),
    Column('crew_id', String, ForeignKey('crew.page_ref')),
    Column('role_id', Integer, ForeignKey('role.id')),
    Column('rank', Integer),
)

# Theme / Film_Theme
Theme = Table(
    'theme', metadata,
    Column('id', Integer, primary_key=True),
    Column('theme_ref', String),
)

Film_Theme = Table(
    'film_theme', metadata,
    Column('film_id', String, ForeignKey('film.page_ref')),
    Column('theme_id', Integer, ForeignKey('theme.id')),
)

# Tags / Film_Tag
Tag = Table(
    'tag', metadata,
    Column('id', Integer, primary_key=True),
    Column('tag_ref', String),
)

Film_Tag = Table(
    'film_tag', metadata,
    Column('film_id', String, ForeignKey('film.page_ref')),
    Column('tag_id', Integer, ForeignKey('tag.id')),
)

# Ratings
Rating = Table(
    'user_rating', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', String),
    Column('film_id', String),
    Column('rating', Float),
    Column('liked', Boolean),
)
