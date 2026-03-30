import time

import httpx
from loguru import logger

from sources.base import SourceBase

from .problems import problems
from .solutions import solutions


class SDUT(SourceBase):
    source = "sdut"

    @staticmethod
    def problem_url(pid: str):
        return f"https://oj.sdutacm.cn/onlinejudge3/problems/{pid}"

    @staticmethod
    def user_url(username: str):
        return f"https://oj.sdutacm.cn/onlinejudge3/users/{username}"

    @staticmethod
    async def login(username: str, password: str):
        logger.info(f"SDUT login attempt: username={username}")
        async with httpx.AsyncClient() as client:
            session_url = "https://oj.sdutacm.cn/onlinejudge3/api/getSession?t=" + str(
                time.time() * 1000
            )
            resp = await client.get(session_url)
            csrf = resp.cookies.get("csrfToken")
            headers = {"x-csrf-token": csrf}
            login_url = "https://oj.sdutacm.cn/onlinejudge3/api/login"
            resp = await client.post(
                login_url,
                json={"loginName": username, "password": password},
                headers=headers,
            )
            success = resp.json()["success"] is True
            if success:
                logger.success(f"SDUT login successful: username={username}")
            else:
                logger.warning(f"SDUT login failed: username={username}")
            return success

    @staticmethod
    async def problems():
        await problems()

    @staticmethod
    async def solutions():
        await solutions()
