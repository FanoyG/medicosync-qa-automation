import httpx

async def test_app_health(client: httpx.AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data['status'] == "Healthy"
    assert data['status_code'] == 200