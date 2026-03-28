import httpx
import time


class SDUT:
    source = "sdut"

    @staticmethod
    def problem_url(pid: str):
        return f"https://oj.sdutacm.cn/onlinejudde3/problems/{pid}"

    @staticmethod
    def user_url(username: str):
        return f"https://oj.sdutacm.cn/onlinejudge3/users/{username}"

    @staticmethod
    async def login(username: str, password: str):
        async with httpx.AsyncClient() as client:
            session_url = (
                "https://acm.sdut.edu.cn/onlinejudge3/api/getSession?t="
                + str(time.time() * 1000)
            )
            resp = await client.get(session_url)
            csrf = resp.cookies.get("csrfToken")
            headers = {"x-csrf-token": csrf}
            login_url = "https://acm.sdut.edu.cn/onlinejudge3/api/login"
            resp = await client.post(
                login_url,
                json={"loginName": username, "password": password},
                headers=headers,
            )
            return resp.json()["success"] is True
