def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_deep_health_endpoint(client):
    response = client.get("/health/deep")
    assert response.status_code == 200
    data = response.get_json()
    assert data["db"] == "ok"
    assert data["redis"] == "ok"