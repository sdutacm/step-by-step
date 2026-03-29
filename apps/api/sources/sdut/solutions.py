import time
from datetime import datetime, timedelta
from typing import List

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from db.models.problem import Problem
from db.models.solution import Solution
from db.session import SessionLocal
from schemas.language import LanguageEnum
from schemas.result import ResultEnum


def to_language_enum(raw_language: str) -> LanguageEnum:
    language = LanguageEnum.Unknown
    raw_language = raw_language.lower()
    if raw_language == "gcc" or raw_language == "c":
        language = LanguageEnum.C
    elif raw_language == "g++" or raw_language == "c++":
        language = language.Cpp
    elif (
        raw_language == "python2"
        or raw_language == "python3"
        or raw_language == "python"
    ):
        language = language.Python
    elif raw_language == "go":
        language = language.Go
    elif raw_language == "rust":
        language = language.Rust
    elif raw_language == "javascript":
        language = language.JavaScript
    elif raw_language == "java":
        language = language.Java
    elif raw_language == "typescript":
        language = language.TypeScript
    elif raw_language == "c#":
        language = language.CSharp
    elif raw_language == "pascal":
        language = language.Pascal
    return language


def to_result_enum(raw_result: int) -> ResultEnum:
    result = ResultEnum.Unknown
    if raw_result == 1:
        result = ResultEnum.Accepted
    elif raw_result == 2:
        result = ResultEnum.TimeLimitExceeded
    elif raw_result == 3:
        result = ResultEnum.MemoryLimitExceeded
    elif raw_result == 4:
        result = ResultEnum.WrongAnswer
    elif raw_result == 5:
        result = ResultEnum.RuntimeError
    elif raw_result == 6:
        result = ResultEnum.OutputLimitExceeded
    elif raw_result == 7:
        result = ResultEnum.CompileError
    elif raw_result == 8:
        result = ResultEnum.PresentationError
    elif raw_result == 11:
        result = ResultEnum.SystemError
    return result


async def get_csrf(client: httpx.AsyncClient):
    session_url = "https://oj.sdutacm.cn/onlinejudge3/api/getSession?t=" + str(
        time.time() * 1000
    )
    resp = await client.get(session_url)
    csrf = resp.cookies["csrfToken"]
    return csrf


async def login(client: httpx.AsyncClient):
    username = settings.SDUT_SPIDER_USER
    password = settings.SDUT_SPIDER_PASS
    login_url = "https://oj.sdutacm.cn/onlinejudge3/api/login"
    logger.info(f"[SDUT] Logging in as {username}")
    resp = await client.post(
        login_url,
        json={"loginName": username, "password": password},
    )
    success = resp.json()["success"] is True
    if success:
        logger.success("[SDUT] Login successful")
    else:
        logger.error(f"[SDUT] Login failed: {resp.json()}")
    return success


async def fetch_solutions(
    client: httpx.AsyncClient, session: Session
) -> List[Solution]:
    url = "https://oj.sdutacm.cn/onlinejudge3/api/getSolutionList"
    solution = session.query(Solution).order_by(-Solution.solution_id).first()
    sid = int(solution.solution_id) if solution is not None else 0
    logger.info(f"[SDUT] Starting solutions sync from solution_id > {sid}")
    params = {"gt": sid, "limit": 1000, "order": [["solutionId", "DESC"]]}

    total_new = 0
    total_updated = 0
    page = 0

    while True:
        page += 1
        resp = await client.post(url, json=params)
        resp = resp.json()
        rows = resp["data"]["rows"]
        need_break = False
        new_count = 0
        updated_count = 0

        for row in rows:
            existing = (
                session.query(Solution)
                .filter(Solution.solution_id == str(row["solutionId"]))
                .first()
            )
            is_new = existing is None
            if is_new:
                solution = Solution()
                new_count += 1
            else:
                solution = existing
                updated_count += 1

            problem_id = str(row["problem"]["problemId"])
            problem = (
                session.query(Problem)
                .filter(
                    Problem.source == "sdut",
                    Problem.problem_id == problem_id,
                )
                .first()
            )
            if problem is None:
                logger.warning(
                    f"[SDUT] Problem {problem_id} not found, skipping solution"
                )
                continue

            solution.solution_id = str(row["solutionId"])
            result = to_result_enum(row["result"])
            if result == ResultEnum.Unknown:
                logger.warning(f"[SDUT] Unknown result code: {row['result']}")
            language = to_language_enum(row["language"])
            if language == LanguageEnum.Unknown:
                logger.warning(f"[SDUT] Unknown language: {row['language']}")
            solution.result = result
            solution.language = language
            solution.submitted_at = datetime.strptime(
                row["createdAt"], "%Y-%m-%dT%H:%M:%S.000Z"
            ) + timedelta(hours=8)
            solution.source = "sdut"
            solution.problem = problem
            solution.username = row["user"]["userId"]
            solution.nickname = row["user"]["nickname"]

            session.add(solution)

            if row["result"] == -1 and (
                datetime.now() - solution.submitted_at
            ) < timedelta(days=1):
                need_break = True
                break

        total_new += new_count
        total_updated += updated_count

        if len(rows) < 1000:
            need_break = True

        logger.info(
            f"[SDUT] Page {page}: processed {new_count} new, {updated_count} updated"
        )

        if need_break is True:
            break
        session.commit()

    logger.info(
        f"[SDUT] Solutions sync completed: {total_new} new, {total_updated} updated"
    )
    return []


async def solutions():
    logger.info("[SDUT] Starting solutions sync")
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            csrf_token = await get_csrf(client)
            client.headers.update({"x-csrf-token": csrf_token})
            await login(client)
            solus = await fetch_solutions(client, session)
        session.commit()
    logger.info("[SDUT] Solutions sync finished")


if __name__ == "__main__":
    import asyncio

    asyncio.run(solutions())
