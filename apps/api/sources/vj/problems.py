from typing import List

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from db.models.problem import Problem
from db.session import SessionLocal


async def login(client: httpx.AsyncClient):
    username = settings.VJ_SPIDER_USER
    password = settings.VJ_SPIDER_PASS
    login_url = "https://vjudge.net/user/login"
    logger.info(f"[VJ] Logging in as {username}")
    resp = await client.post(
        login_url,
        data={"username": username, "password": password},
    )
    success = resp.text == "success"
    if success:
        logger.success("[VJ] Login successful")
    else:
        logger.error(f"[VJ] Login failed: {resp.text}")
    return success


async def fetch_problems(client: httpx.AsyncClient, session: Session) -> List[Problem]:
    logger.info("[VJ] Fetching problems list")
    url = "https://vjudge.net/problem/data"
    page = 0
    probs = []
    total_fetched = 0

    while True:
        page += 1
        resp = await client.get(
            url,
            params={
                "start": page * 100,
                "length": 100,
                "OJId": "All",
                "category": "all",
            },
        )
        rows = resp.json()["data"]
        row_count = len(rows)
        total_fetched += row_count
        logger.debug(f"[VJ] Page {page}: fetched {row_count} problems")

        for row in rows:
            title = row["title"]
            problem_id = f"{row['originOJ']}-{row['originProb']}"
            prob = (
                session.query(Problem)
                .filter(
                    Problem.source == "vj",
                    Problem.problem_id == problem_id,
                )
                .first()
            )
            if prob is None:
                prob = Problem()
                probs.append(prob)
                logger.debug(f"[VJ] New problem: {problem_id}")
            prob.problem_id = problem_id
            prob.title = title
            prob.source = "vj"
            session.add(prob)
        session.commit()

        if row_count < 100:
            break

    logger.info(f"[VJ] Problems fetched: {total_fetched} total, {len(probs)} new")
    return probs


async def problems():
    logger.info("[VJ] Starting problems sync")
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            await login(client)
            probs = await fetch_problems(client, session)
        session.commit()
    logger.success(f"[VJ] Problems sync completed: {len(probs)} new problems")


if __name__ == "__main__":
    import asyncio

    asyncio.run(problems())
