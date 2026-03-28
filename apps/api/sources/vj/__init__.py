import httpx


class VJ:
    @staticmethod
    def problem_url(pid: str):
        return f"https://vjudge.net/problem/{pid}"

    @staticmethod
    def user_url(user_id: str):
        return f"https://vjudge.net/user/{user_id}"

    @staticmethod
    async def login(username: str, password: str):
        async with httpx.AsyncClient() as client:
            login_url = "https://vjudge.net/user/login"
            resp = await client.post(
                login_url, data={"username": username, "password": password}
            )
            return resp.text == "success"
