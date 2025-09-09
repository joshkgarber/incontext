import pytest
from incontext.db import get_db


def test_index(client, auth):
    response = client.get('/contexts/') # when not logged in each page shows links to log in or register. 
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/contexts/') # the index view should display information about the post that was added with the test data.
    assert b'Log Out' in response.data # when logged in there's a ling to log out.
    assert b'test name' in response.data
    assert b'Created: 01.01.2025' in response.data
    assert b'Creator: test' in response.data
    assert b'test\ndescription' in response.data
    assert b'href="/contexts/1/update"' in response.data


@pytest.mark.parametrize('path', (
    'contexts/create',
    'contexts/1/update',
    'contexts/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


def test_creator_required(app, client, auth):
    # change the context creator to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE contexts SET creator_id = 3 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify another user's context
    assert client.post('contexts/1/update').status_code == 403
    assert client.post('contexts/1/delete').status_code == 403
    # current user doesn't see Edit link
    assert b'href="/contexts/1/update"' not in client.get('/contexts').data


@pytest.mark.parametrize('path', (
    'contexts/2/update',
    'contexts/2/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('contexts/create').status_code == 200

    response = client.post('contexts/create', data={'name': 'created', 'description': 'description'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM contexts').fetchone()[0]
        assert count == 2
    

def test_update(client, auth, app):
    auth.login()
    assert client.get('contexts/1/update').status_code == 200
    
    client.post('/contexts/1/update', data={'name': 'updated', 'description': 'updated description'})

    with app.app_context():
        db = get_db()
        context = db.execute('SELECT * FROM contexts WHERE id = 1').fetchone()
        assert context['name'] == 'updated'
        assert context['description'] == 'updated description'


@pytest.mark.parametrize('path', (
    '/contexts/create',
    '/contexts/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'name': '', 'description': ''})
    assert b'Name and description are required' in response.data

    response = client.post(path, data={'name': 'name', 'description': ''})
    assert b'Name and description are required' in response.data
    
    response = client.post(path, data={'name': '', 'description': 'description'})
    assert b'Name and description are required' in response.data
    

def test_delete(client, auth, app): # the delete view should should redirect to the index url and the post should no longer exist in the db.
    auth.login()
    response = client.post('/contexts/1/delete')
    assert response.headers['Location'] == '/contexts/'

    with app.app_context():
        db = get_db()
        context = db.execute('SELECT * FROM contexts WHERE id = 1').fetchone()
        assert context is None


