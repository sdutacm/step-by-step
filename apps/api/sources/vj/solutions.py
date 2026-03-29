from datetime import datetime

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from db.models.problem import Problem
from db.models.solution import Solution
from db.session import SessionLocal
from schemas.language import LanguageEnum
from schemas.result import ResultEnum


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
        logger.success(f"[VJ] Login successful")
    else:
        logger.error(f"[VJ] Login failed: {resp.text}")
    return success


def vj_item_to_solution(user: str, item: dict) -> dict:
    data = {
        "problem": item[0] + "-" + item[1],
        "time_used": item[2],
        "memory_used": item[3],
        "code_len": item[4],
        "username": user,
        "nickname": user,
        # 返回数据中没有语言信息
        "language": LanguageEnum.Unknown.name,
    }
    # 如果没有 AC 时间，则说明这个题目还没通过
    if item[5] is None:
        # 只知道没 AC，但不知道具体是什么结果
        data["result"] = ResultEnum.Unknown.name
        data["submitted_at"] = datetime.fromtimestamp(item[6])
    else:
        data["result"] = ResultEnum.Accepted.name
        data["submitted_at"] = datetime.fromtimestamp(item[5])
    return data


async def fetch_solutions(client: httpx.AsyncClient, session: Session):
    logger.info("[VJ] Fetching solutions from group sdutsbs")
    url = "https://vjudge.net/group/solveEntries/sdutsbs?queryWindowMillis=7200000"
    resp = await client.get(url)
    data = resp.json()
    user_count = len(data)
    total_solutions = sum(len(rows) for rows in data.values())
    logger.info(f"[VJ] Found {user_count} users with {total_solutions} total solutions")

    for user, rows in data.items():
        logger.debug(f"[VJ] Processing user {user}: {len(rows)} solutions")
        session.query(Solution).where(
            Solution.source == "vj", Solution.username == user
        ).delete()
        new_count = 0
        for row in rows:
            params = vj_item_to_solution(user, row)
            problem = (
                session.query(Problem)
                .where(Problem.source == "vj", Problem.problem_id == params["problem"])
                .first()
            )
            if problem is None:
                problem = Problem()
                problem.problem_id = params["problem"]
                problem.title = params["problem"]
                problem.source = "vj"
                session.add(problem)
                session.commit()
                logger.debug(f"[VJ] Created new problem: {problem.problem_id}")
            solution = Solution()
            solution.source = "vj"
            solution.username = user
            solution.nickname = user
            solution.solution_id = 0
            solution.language = params["language"]
            solution.result = params["result"]
            solution.submitted_at = params["submitted_at"]
            solution.problem = problem
            session.add(solution)
            new_count += 1
        session.commit()
        logger.info(f"[VJ] Saved {new_count} solutions for user {user}")
    logger.success(
        f"[VJ] Solutions sync completed: {total_solutions} solutions processed"
    )


async def solutions():
    logger.info("[VJ] Starting solutions sync")
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            await login(client)
            await fetch_solutions(client, session)
        session.commit()
    logger.info("[VJ] Solutions sync finished")


if __name__ == "__main__":
    import asyncio

    asyncio.run(solutions())
