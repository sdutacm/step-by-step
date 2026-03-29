import math
import time
from typing import List

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from db.models.problem import Problem
from db.session import SessionLocal


async def get_csrf(client: httpx.AsyncClient):
    session_url = "https://oj.sdutacm.cn/onlinejudge3/api/getSession?t=" + str(
        time.time() * 1000
    )
    resp = await client.get(session_url)
    csrf = resp.cookies["csrfToken"]
    logger.debug("[SDUT] CSRF token obtained")
    return csrf


async def fetch_problems(client: httpx.AsyncClient, session: Session) -> List[Problem]:
    logger.info("[SDUT] Fetching problems list")
    url = "https://oj.sdutacm.cn/onlinejudge3/api/getProblemList"
    page = 1
    resp = await client.post(url, json={"limit": 20, "page": 1})
    resp = resp.json()
    page = resp["data"]["page"]
    count = resp["data"]["count"]
    total_pages = math.ceil(count / 20)
    probs = []
    logger.info(f"[SDUT] Total problems: {count}, pages: {total_pages}")

    for page in range(1, total_pages + 1):
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
                logger.debug(f"[SDUT] New problem: {row['problemId']}")
            prob.problem_id = str(row["problemId"])
            prob.title = row["title"]
            prob.source = "sdut"
            session.add(prob)
        if page % 10 == 0:
            logger.info(f"[SDUT] Progress: page {page}/{total_pages}")
    return probs


async def problems():
    logger.info("[SDUT] Starting problems sync")
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            csrf_token = await get_csrf(client)
            client.headers.update({"x-csrf-token": csrf_token})
            probs = await fetch_problems(client, session)
        session.commit()
    logger.success(f"[SDUT] Problems sync completed: {len(probs)} new problems")


if __name__ == "__main__":
    import asyncio

    asyncio.run(problems())
