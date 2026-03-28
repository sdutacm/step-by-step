class SourceBase:
    source = "source"

    @staticmethod
    def problem_url(pid: str):
        pass

    @staticmethod
    def user_url(username: str):
        pass

    @staticmethod
    async def login(username: str, password: str):
        pass

    @staticmethod
    async def problems():
        pass

    @staticmethod
    async def solutions():
        pass
