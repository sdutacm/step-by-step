import math
import time
from typing import List

import httpx
from loguru import logger

from db.models.problem import Problem
from db.session import SessionLocal


async def get_csrf(client: httpx.AsyncClient):
    session_url = "https://oj.sdutacm.cn/onlinejudge3/api/getSession?t=" + str(
        time.time() * 1000
    )
    resp = await client.get(session_url)
    csrf = resp.cookies["csrfToken"]
    return csrf


async def fetch_problems(client: httpx.AsyncClient) -> List[Problem]:
    url = "https://oj.sdutacm.cn/onlinejudge3/api/getProblemList"
    page = 1
    # 先进行一次请求，获取总量
    resp = await client.post(url, json={"limit": 20, "page": 1})
    resp = resp.json()
    page = resp["data"]["page"]
    count = resp["data"]["count"]
    probs = []
    for page in range(1, math.ceil(count / 20) + 1):
        resp = await client.post(url, json={"limit": 20, "page": page})
        rows = resp.json()["data"]["rows"]
        for row in rows:
            prob = Problem()
            prob.problem_id = str(row["problemId"])
            prob.title = row["title"]
            probs.append(prob)
    return probs


async def problems():
    logger.info("Hello World!")
    async with httpx.AsyncClient() as client:
        csrf_token = await get_csrf(client)
        client.headers.update({"x-csrf-token": csrf_token})
        probs = await fetch_problems(client)
    with SessionLocal() as session:
        for prob in probs:
            session.merge(prob)
        session.commit()


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(problems())
