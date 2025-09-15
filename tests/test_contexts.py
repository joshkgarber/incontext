import pytest
from incontext.db import get_db, dict_factory
from incontext.lists import get_user_lists
from incontext.contexts import get_unrelated_lists


def test_index(client, auth):
    # User must be logged in
    response = client.get("/contexts/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/contexts/")
    assert response.status_code == 200
    # Shows contexts owned by the user
    assert b"context name 1" in response.data
    assert b"context description 1" in response.data
    assert b"context name 2" in response.data
    assert b"context description 2" not in response.data
    assert b"context name 3" in response.data
    assert b"context description 3" not in response.data


def test_view(client, auth, app):
    path = "/contexts/1/view"
    # You must be logged in and have access to view a context
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get(path)
    assert response.status_code == 403
    auth.login()
    response = client.get(path)
    assert response.status_code == 200
    # Shows connected lists and agents
    assert b"list name 1" in response.data
    assert b"list name 2" in response.data
    assert b"master list name 1" in response.data
    # Doesn't show other lists
    assert b"list name 3" not in response.data
    assert b"list name 4" not in response.data
    assert b"list name 5" not in response.data
    assert b"master list name 2" not in response.data
    assert b"master list name 3" not in response.data


def test_connect_list(client, auth, app):
    path = "/contexts/1/new-list"
    # Get requests
    # Must be logged in and own the context
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get(path)
    assert response.status_code == 403
    with app.app_context():
        auth.login()
        response = client.get(path)
        assert response.status_code == 200
        # The user's lists are shown (if not already connected)
        assert b"<h3>list name 1" not in response.data
        assert b"<h3>list name 2" not in response.data
        assert b"<h3>list name 3" not in response.data
        assert b"<h3>list name 4" not in response.data
        assert b"<h3>master list name 1" not in response.data
        assert b"<h3>master list name 2" in response.data
    # Post requests
    auth.logout()
    # Must be logged in and own the context
    response = client.post(path)
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get(path)
    assert response.status_code == 403
    auth.login()
    response = client.get(path)
    assert response.status_code == 200
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        context_list_relations_before = db.execute("SELECT * FROM context_list_relations").fetchall()
        # Must own the list
        auth.login()
        data = dict(list_id="3")
        response = client.post(path, data=data)
        assert response.status_code == 403
        # List-context relation gets saved
        data = dict(list_id="5")
        response = client.post(path, data=data)
        context_list_relations_after = db.execute("SELECT * FROM context_list_relations").fetchall()
        assert len(context_list_relations_after) == len(context_list_relations_before) + 1
        # Redirected to view context
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/1/view"


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


