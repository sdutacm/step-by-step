from datetime import datetime

import httpx
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
    resp = await client.post(
        login_url,
        data={"username": username, "password": password},
    )
    success = resp.text == "success"
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
    # 根据 VJ 说明，此接口用于获取当前 group（sdutsbs） 一天内登录过的用户的所有 AC 数据
    url = "https://vjudge.net/group/solveEntries/sdutsbs?queryWindowMillis=7200000"
    resp = await client.get(url)
    for user, rows in resp.json().items():
        # vj 的返回数据中没有 solution id，因此我们无法进行更新，只能全量覆盖
        session.query(Solution).where(
            Solution.source == "vj", Solution.username == user
        ).delete()
        for row in rows:
            # 因为 VJ 限制题目获取，此处的题目可能不在 problems 中，所以需要更新 problems
            params = vj_item_to_solution(user, row)
            problem = (
                session.query(Problem)
                .where(Problem.source == "vj", Problem.problem_id == params["problem"])
                .first()
            )
            if problem is None:
                problem = Problem()
                problem.problem_id = params["problem"]
                # 因为数据里没有，所以用 pid 填充
                problem.title = params["problem"]
                session.add(problem)
                session.commit()
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
        session.commit()


async def solutions():
    with SessionLocal() as session:
        async with httpx.AsyncClient() as client:
            await login(client)
            await fetch_solutions(client, session)
        session.commit()
