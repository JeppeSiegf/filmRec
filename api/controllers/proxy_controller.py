from flask_restx import Namespace, Resource
from flask import request, Response
import requests

api = Namespace('proxy', description='Image proxy operations')


@api.route('/image')
class ProxyImage(Resource):
    def get(self):
        """Proxies external image URLs to bypass CORS issues"""
        image_url = request.args.get('url')
        if not image_url:
            return {"error": "Missing 'url' parameter"}, 400

        try:
            resp = requests.get(image_url, stream=True)
            resp.raise_for_status()
            return Response(
                resp.content,
                content_type=resp.headers.get('Content-Type', 'image/jpeg')
            )
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}, 500
