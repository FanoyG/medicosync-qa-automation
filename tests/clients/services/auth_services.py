from tests.clients.request_builder import RequestBuilder

class AuthService:
    def __init__(self, client):
        self.client = client

    async def register(self, payload: dict):
        return await (
            RequestBuilder(self.client)
            .set_path("/auth/register")
            .set_json(payload)
            .send("POST")
        )

    async def login(self, payload: dict):
        return await (
            RequestBuilder(self.client)
            .set_path("/auth/login")
            .set_json(payload)
            .send("POST")
        )