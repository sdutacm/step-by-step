import httpx


class VJ:
    source = "vj"

    @staticmethod
    def problem_url(pid: str):
        return f"https://vjudge.net/problem/{pid}"

    @staticmethod
    def user_url(username: str):
        return f"https://vjudge.net/user/{username}"

    @staticmethod
    async def login(username: str, password: str):
        async with httpx.AsyncClient() as client:
            login_url = "https://vjudge.net/user/login"
            resp = await client.post(
                login_url, data={"username": username, "password": password}
            )
            return resp.text == "success"

    @staticmethod
    async def problems():
        pass

    @staticmethod
    async def solutions():
        pass
