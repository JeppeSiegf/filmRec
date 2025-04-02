from api import api
from flask_restx import fields, Model

film_model = api.model('Film', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'image_ref': fields.String(description='Image Reference URL for the film'),
    'image_ref_large': fields.String(description='Higher quality image ref'),
    'banner_ref': fields.String(description='URL ref for background image for film'),
    'title': fields.String(description='The film title'),
    'title_original': fields.String(description='Name of film in original language'),
    'description': fields.String(description='Synopsis of plot'),
    'total_watches' : fields.Integer(description='Amount people who have logged the film'),
    'runtime': fields.Integer(description='Length of film'),
    'release_year': fields.Integer(description='Year of release'),
    'genres': fields.List(fields.String, description='List of genres'),
    'languages': fields.List(fields.String, description='List of languages spoken in film'),
    'crew_members': fields.List(
        fields.Nested(api.model('CrewMember', {
            'page_ref': fields.String(description="Reference URL for the crew member"),
            'name': fields.String(description="Crew member's name"),
            'role': fields.String(description="Role of the crew member"),
        })),

    ),
    'roles': fields.List(fields.String, description='Crews role during production')
})


film_model_simple = api.model('Search_Result', {
    'page_ref': fields.String(required=True, description='Reference URL for the film'),
    'title': fields.String(description='The film title'),
    'release_year': fields.Integer(description='Year of release'),
})
