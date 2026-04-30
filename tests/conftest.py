import pytest
from app import create_app

@pytest.fixture
def client():
	app = create_app("testing")
	app.config["TESTING"] = True
	with app.test_client() as client:
		with app.app_context():
			yield client
