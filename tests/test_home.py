import pytest


def test_index(client, auth):
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'

    auth.login()
    response = client.get('/') # the index view should display.
    assert response.status_code == 200
