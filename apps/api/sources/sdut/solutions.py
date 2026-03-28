import time
from datetime import datetime, timedelta
from typing import List

import httpx
from app.core.config import settings
from db.models.problem import Problem
from db.models.solution import Solution
from db.session import SessionLocal
from loguru import logger
from schemas.language import LanguageEnum
from schemas.result import ResultEnum
from sqlalchemy.orm import Session


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
    resp = await client.post(
        login_url,
        json={"loginName": username, "password": password},
    )
    success = resp.json()["success"] is True
    return success


async def fetch_solutions(
    client: httpx.AsyncClient, session: Session
) -> List[Solution]:
    url = "https://oj.sdutacm.cn/onlinejudge3/api/getSolutionList"
    # 从已有数据中找出已获取的 solution id 最高的
    solution = session.query(Solution).order_by(-Solution.solution_id).first()
    sid = int(solution.solution_id) if solution is not None else 0
    # 从上次获取到的位置开始，更新数据
    params = {"gt": sid, "limit": 1000, "order": [["solutionId", "DESC"]]}

    while True:
        resp = await client.post(url, json=params)
        resp = resp.json()
        rows = resp["data"]["rows"]
        need_break = False

        for row in rows:
            solution = (
                session.query(Solution)
                .filter(Solution.solution_id == str(row["solutionId"]))
                .first()
            )
            if solution is None:
                solution = Solution()
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
                logger.warning(f"problem {problem_id} not found!")
                continue

            solution.solution_id = str(row["solutionId"])
            result = to_result_enum(row["result"])
            if result == ResultEnum.Unknown:
                logger.warning(f"result {row['result']} unknown")
            language = to_language_enum(row["language"])
            if language == LanguageEnum.Unknown:
                logger.warning(f"language {row['language']} unknown")
            solution.result = result
            solution.language = language
            solution.submitted_at = datetime.strptime(
                row["createdAt"], "%Y-%m-%dT%H:%M:%S.000Z"
            ) + timedelta(hours=8)
            solution.source = "sdut"
            solution.problem = problem

            # sdut 平台的 username 使用 user id
            solution.username = row["user"]["userId"]
            solution.nickname = row["user"]["nickname"]

            session.add(solution)

            # 如果状态为评测中，且提交时间在一天内，则退出获取
            if row["result"] == -1 and (
                datetime.now() - solution.submitted_at
            ) < timedelta(days=1):
                need_break = True
                break

        # 如果数量不够，认为是获取结束了
        if len(rows) < 1000:
            need_break = True

        if need_break is True:
            break
        session.commit()

    return []


async def solutions():
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            csrf_token = await get_csrf(client)
            client.headers.update({"x-csrf-token": csrf_token})
            await login(client)
            solus = await fetch_solutions(client, session)
        session.commit()
        logger.info(f"本次抓取 solutions count = {len(solus)}")
