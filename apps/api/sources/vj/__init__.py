import httpx
from loguru import logger

from sources.base import SourceBase
from .problems import problems
from .solutions import solutions


class VJ(SourceBase):
    source = "vj"

    @staticmethod
    def problem_url(pid: str):
        return f"https://vjudge.net/problem/{pid}"

    @staticmethod
    def user_url(username: str):
        return f"https://vjudge.net/user/{username}"

    @staticmethod
    async def login(username: str, password: str):
        logger.info(f"VJ login attempt: username={username}")
        async with httpx.AsyncClient() as client:
            login_url = "https://vjudge.net/user/login"
            resp = await client.post(
                login_url, data={"username": username, "password": password}
            )
            success = resp.text == "success"
            if success:
                logger.success(f"VJ login successful: username={username}")
            else:
                logger.warning(f"VJ login failed: username={username}")
            return success

    @staticmethod
    async def problems():
        await problems()

    @staticmethod
    async def solutions():
        await solutions()
