import aiohttp


class SessionManager:
    _shared_session = None

    @classmethod
    async def enable_shared_session(cls):

        if cls._shared_session is None or cls._shared_session.closed:
            timeout = aiohttp.ClientTimeout(
                total=None,
                connect=300,
                sock_connect=300,
                sock_read=300
            )
            connector = aiohttp.TCPConnector(limit_per_host=100, force_close=False, ssl=False)
            cls._shared_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Connection': 'keep-alive'}
            )

    @classmethod
    async def disable_shared_session(cls):
        """
        Closes and clears the shared session.
        """
        if cls._shared_session and not cls._shared_session.closed:
            await cls._shared_session.close()
            cls._shared_session = None





