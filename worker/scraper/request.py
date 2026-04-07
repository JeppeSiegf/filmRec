import json
import logging
import os

import aiohttp
from aiohttp import ClientResponseError
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


class APIService:

    def __init__(self):

        self.api_address = os.getenv('API_ADDRESS')

    async def fetch_latest_film(self):

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_address}/api/films/latest") as response:
                if response.status == 404:
                    return None

                response.raise_for_status()
                return await response.json()

    async def fetch_latest_ratings(self, user_id, session):

        async with session.get(f"{self.api_address}/ratings/latest/{user_id}") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.json()  # assume JSON with a 'film_id' field

    async def post_latest_ratings(self, user_id, session):

        async with session.get(f"{self.api_address}/ratings/latest/{user_id}") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.json()  # assume JSON with a 'film_id' field

    async def post_films(self, films):

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.api_address}/api/films/",
                    json=films
            ) as response:
                if response.status == 404:
                    return None
                response.raise_for_status()
                return await response.json()

    async def put_films(self, films):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                    f"{self.api_address}/api/films/",
                    json=films
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def post_users(self, users):

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.api_address}/api/users/",
                    json=users
            ) as response:
                if response.status == 404:
                    return None
                response.raise_for_status()
                return await response.json()

    async def post_ratings(self, ratings):

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.api_address}/api/ratings/",
                    json=ratings
            ) as response:
                if response.status == 404:
                    return None
                response.raise_for_status()
                return await response.json()


    async def test(self):
        return 'working connection'
