from app import app

def test_shopping_cart():
    response = app.test_client().get('/')
    assert response.status_code == 200
