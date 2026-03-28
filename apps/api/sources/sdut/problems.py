import math
import time
from typing import List

import httpx
from db.models.problem import Problem
from db.session import SessionLocal
from loguru import logger
from sqlalchemy.orm import Session


async def get_csrf(client: httpx.AsyncClient):
    session_url = "https://oj.sdutacm.cn/onlinejudge3/api/getSession?t=" + str(
        time.time() * 1000
    )
    resp = await client.get(session_url)
    csrf = resp.cookies["csrfToken"]
    return csrf


async def fetch_problems(client: httpx.AsyncClient, session: Session) -> List[Problem]:
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
            prob = (
                session.query(Problem)
                .filter(
                    Problem.source == "sdut",
                    Problem.problem_id == str(row["problemId"]),
                )
                .first()
            )
            if prob is None:
                prob = Problem()
                probs.append(prob)
            prob.problem_id = str(row["problemId"])
            prob.title = row["title"]
            prob.source = "sdut"
            session.add(prob)
            logger.info(f"update sdut problem title = {prob.title}")
    return probs


async def problems():
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            csrf_token = await get_csrf(client)
            client.headers.update({"x-csrf-token": csrf_token})
            probs = await fetch_problems(client, session)
        session.commit()
        logger.info(f"本次抓取 problems count = {len(probs)}")
