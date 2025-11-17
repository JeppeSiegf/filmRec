from flask_restx import fields
from .. import api

film_model = api.model('Film', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'image_ref': fields.String(description='Image Reference URL for the film'),
    'image_ref_large': fields.String(description='Higher quality image ref'),
    'banner_ref': fields.String(description='URL ref for background image for film'),
    'title': fields.String(description='The film title'),
    'title_original': fields.String(description='Name of film in original language'),
    'description': fields.String(description='Synopsis of plot'),
    'total_watches': fields.Integer(description='Amount people who have logged the film'),
    'runtime': fields.Integer(description='Length of film'),
    'release_year': fields.Integer(description='Year of release'),
    'avg_rating': fields.Float(description='Average Letterboxd rating'),
    'imdb_rating': fields.Float(description='Average IMDB rating'),
    'imdb_ref': fields.String(destripotion = "ID to movies imdb page"),
    'series': fields.String(description='Reference to series Film is part of'),
    'series_id': fields.Integer(attribute='series_id', description='Reference to series Film is part of'),
    'genres': fields.List(fields.String, description='List of genres'),
    'languages': fields.List(fields.String, description='List of languages spoken in film'),
    'crew_members': fields.List(
        fields.Nested(api.model('CrewMember', {
            'page_ref': fields.String(description="Reference URL for the crew member"),
            'name': fields.String(description="Crew member's name"),
            'role': fields.String(description="Role of the crew member"),
            'rank': fields.Integer(description="Crew members spot on billing order")
        })),

    ),
    'roles': fields.List(fields.String, description='Crews role during production')
})

film_model_simple = api.model('Search_Result', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'title': fields.String(description='The film title'),
    'release_year': fields.Integer(description='Year of release'),
})

film_model_bulk = api.model('Film', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'title': fields.String(description='The film title'),
    'title_original': fields.String(description='Original language title'),
    'description': fields.String(description='Synopsis of plot'),
    'image_ref': fields.String(description='Poster image URL'),
    'image_ref_large': fields.String(description='High quality poster URL'),
    'banner_ref': fields.String(description='Background banner URL'),
    'release_year': fields.Integer(description='Year of release'),
    'runtime': fields.Integer(description='Film runtime in minutes'),
    'total_watches': fields.Integer(description='Number of people who watched'),
    'genres': fields.List(fields.String, description='List of genres'),
    'languages': fields.List(fields.Nested(api.model('Language', {
        'name': fields.String(required=True, description='Language name'),
        'is_primary': fields.Boolean(description='Whether it is the primary language')
    })), description='Languages spoken'),
    'crew': fields.List(fields.Nested(api.model('CrewMember', {
        'role': fields.String(required=True, description='Role in production'),
        'ref': fields.String(required=True, description='Reference ID for crew member'),
        'name': fields.String(required=True, description='Name of crew member'),
        'rank': fields.Integer(description='Crew member billing rank')
    })), description='Crew members'),
    'cast': fields.List(fields.Nested(api.model('CastMember', {
        'role': fields.String(required=True, description='Role in production'),
        'ref': fields.String(required=True, description='Reference ID for actor'),
        'name': fields.String(required=True, description='Actor name'),
        'rank': fields.Integer(description='Actor billing rank')
    })), description='Cast members'),
    'series_id': fields.String(description='Reference to series if part of one'),
    'imdb_ref': fields.String(description='IMDB reference ID'),
    'avg_rating': fields.Float(description='Average rating')
})

