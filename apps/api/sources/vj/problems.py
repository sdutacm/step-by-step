from typing import List

import httpx
from app.core.config import settings
from db.models.problem import Problem
from db.session import SessionLocal
from loguru import logger
from sqlalchemy.orm import Session


async def login(client: httpx.AsyncClient):
    username = settings.VJ_SPIDER_USER
    password = settings.VJ_SPIDER_PASS
    login_url = "https://vjudge.net/user/login"
    resp = await client.post(
        login_url,
        data={"username": username, "password": password},
    )
    print(resp.text)
    success = resp.text == "success"
    return success


async def fetch_problems(client: httpx.AsyncClient, session: Session) -> List[Problem]:
    url = "https://vjudge.net/problem/data"
    page = 0
    probs = []
    while True:
        resp = await client.get(
            url,
            params={
                "start": page * 100,
                "length": 100,
                "OJId": "All",
                "category": "all",
            },
        )
        page += 1
        rows = resp.json()["data"]
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
            prob.problem_id = problem_id
            prob.title = title
            prob.source = "vj"
            session.add(prob)
            logger.info(f"update vj problem title = {prob.title}")
        session.commit()
        if len(rows) < 100:
            break
    return probs


async def problems():
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            await login(client)
            probs = await fetch_problems(client, session)
        session.commit()
        logger.info(f"本次抓取 problems count = {len(probs)}")
