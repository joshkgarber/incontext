import pytest
from incontext.db import get_db, dict_factory


def test_index(client, auth):
    # user must be logged in
    response = client.get('/master-lists/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-lists/")
    assert response.status_code == 403
    auth.login()
    response = client.get('/master-lists/')
    assert response.status_code == 200
    # test user's master list data gets served
    assert b'master list name 1' in response.data
    assert b'master list description 1' in response.data
    assert b'master list name 2' in response.data
    assert b'master list description 2' in response.data


def test_new_master_list(app, client, auth):
    # user must be logged in
    response = client.get('/master-lists/new')
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("/master-lists/new")
    assert response.status_code == 403
    auth.login()
    response = client.get("/master-lists/new")
    assert response.status_code == 200
    # data validation
    response = client.post(
        'master-lists/new',
        data = {'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    # master list is saved to database
    response = client.post(
        'master-lists/new',
        data = {'name': 'master list name 3', 'description': 'master list description 3'},
    )
    with app.app_context():
        db = get_db()
        master_lists = db.execute('SELECT name, description FROM master_lists WHERE creator_id = 2').fetchall()
        assert len(master_lists) == 3
        assert master_lists[2]['name'] == 'master list name 3'
        assert master_lists[2]['description'] == 'master list description 3'


def test_view_master_list(app, client, auth):
    # user must be logged in
    response = client.get("master-lists/1/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user doesn't have to be admin or creator
    auth.login('other', 'other')
    response = client.get("master-lists/1/view")
    assert response.status_code == 200
    # master list data gets served
    assert b"master list name 1" in response.data
    assert b"master list description 1" in response.data
    assert b"master item name 1" in response.data
    assert b"master item name 2" in response.data
    assert b"master detail name 1" in response.data
    assert b"detail description 1" in response.data
    assert b"master detail name 2" in response.data
    assert b"detail description 2" in response.data
    assert b"master relation content 1" in response.data
    assert b"master relation content 2" in response.data
    assert b"master relation content 3" in response.data
    assert b"master relation content 4" in response.data
    # other master list data does not get served
    assert b"master item name 3" not in response.data
    assert b"master detail name 3" not in response.data
    assert b"master detail description 3" not in response.data
    assert b"master relation content 5" not in response.data
    # list master must exist
    assert client.get("master-lists/4/view").status_code == 404


def test_edit_master_list(app, client, auth):
    # user must be logged in
    response = client.get('/master-lists/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be admin
    auth.login('other', 'other')
    response = client.get("master-lists/1/edit")
    assert response.status_code == 403
    # user must be admin
    auth.login('other', 'other')
    assert client.get('master-lists/1/edit').status_code == 403
    auth.login("admin2", "admin2")
    response = client.get('master-lists/1/edit')
    assert response.status_code == 200
    # master data gets served
    assert b'master list name 1' in response.data
    assert b'master list description 1' in response.data
    # data validation
    response = client.post('master-lists/1/edit', data={'name': '', 'description': ''})
    assert b'Name is required' in response.data
    # changes are saved to database
    response = client.post(
        'master-lists/1/edit',
        data={'name': 'master list name 1 updated', 'description': 'master list description 1 updated'}
    )
    with app.app_context():
        db = get_db()
        master_lists = db.execute('SELECT name, description FROM master_lists').fetchall()
        assert master_lists[0]['name'] == 'master list name 1 updated'
        assert master_lists[0]['description'] == 'master list description 1 updated'
        # other master lists are not changed
        for master_list in master_lists[1:]:
            assert master_list['name'] != 'master list name 1 updated'
            assert master_list['description'] != 'master list description 1 updated'
    # redirected to master_lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == '/master-lists/'
    # master list must exist
    assert client.get('/master-lists/3/edit').status_code == 404


def test_delete_master_list(app, client, auth):
    # user must be logged in
    response = client.post("/master-lists/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login('other', 'other')
    response = client.post("master-lists/1/delete")
    assert response.status_code == 403
    # user must be master list creator
    auth.login("other", "other")
    assert client.post("master-lists/1/delete").status_code == 403
    # master list gets deleted
    auth.login("admin2", "admin2")
    with app.app_context():
        db = get_db()
        master_item_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_items'
        ).fetchone()['count']
        master_detail_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_details'
        ).fetchone()['count']
        master_item_detail_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_item_detail_relations'
        ).fetchone()['count']
        master_list_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_lists'
        ).fetchone()['count']
        master_list_item_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_list_item_relations'
        ).fetchone()['count']
        master_list_detail_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_list_detail_relations'
        ).fetchone()['count']
        affected_master_item_ids = db.execute(
            'SELECT master_item_id FROM master_list_item_relations WHERE master_list_id = 1'
        ).fetchall()
        assert len(affected_master_item_ids) == 2
        affected_master_item_ids = [master_item_id['master_item_id'] for master_item_id in affected_master_item_ids]
        placeholders_affected_master_item_ids = f'{"?, " * len(affected_master_item_ids)}'[:-2]
        affected_master_detail_ids = db.execute(
            'SELECT master_detail_id FROM master_list_detail_relations WHERE master_list_id = 1'
        ).fetchall()
        assert len(affected_master_detail_ids) == 2
        affected_master_detail_ids = [master_detail_id['master_detail_id'] for master_detail_id in affected_master_detail_ids]
        placeholders_affected_master_detail_ids = f'{"?, " * len(affected_master_detail_ids)}'[:-2]
        affected_master_item_and_detail_ids = affected_master_item_ids + affected_master_detail_ids
        affected_master_item_detail_relation_ids = db.execute(
            'SELECT id, master_item_id FROM master_item_detail_relations'
            f' WHERE master_item_id IN ({placeholders_affected_master_item_ids})'
            f' OR master_detail_id IN ({placeholders_affected_master_detail_ids})',
            affected_master_item_and_detail_ids
        ).fetchall()
        assert len(affected_master_item_detail_relation_ids) == 4
        response = client.post('/master-lists/1/delete')
        deleted_master_list = db.execute('SELECT * FROM master_lists WHERE id = 1').fetchone()
        assert deleted_master_list == None
        deleted_master_list_item_relations = db.execute(
            'SELECT * FROM master_list_item_relations WHERE master_list_id = 1'
        ).fetchall()
        assert len(deleted_master_list_item_relations) == 0
        deleted_master_list_detail_relations = db.execute('SELECT * FROM master_list_detail_relations WHERE master_list_id = 1').fetchall()
        assert len(deleted_master_list_detail_relations) == 0
        deleted_master_items = db.execute(
            f'SELECT * FROM master_items WHERE id IN ({placeholders_affected_master_item_ids})',
            affected_master_item_ids
        ).fetchall()
        assert len(deleted_master_items) == 0
        deleted_master_details = db.execute(
            f'SELECT * FROM master_details WHERE id IN ({placeholders_affected_master_detail_ids})',
            affected_master_detail_ids
        ).fetchall()
        assert len(deleted_master_details) == 0
        deleted_master_item_detail_relations = db.execute(
            'SELECT * FROM master_item_detail_relations'
            f' WHERE master_item_id IN ({placeholders_affected_master_item_ids})'
            f' OR master_detail_id IN ({placeholders_affected_master_detail_ids})',
            affected_master_item_and_detail_ids
        ).fetchall()
        assert len(deleted_master_item_detail_relations) == 0
        # other master data does not get deleted
        master_lists = db.execute('SELECT * FROM master_lists').fetchall()
        assert len(master_lists) == master_list_count - 1
        master_items = db.execute('SELECT * FROM master_items').fetchall()
        assert len(master_items) == master_item_count - len(affected_master_item_ids)
        master_list_item_relations = db.execute('SELECT * FROM master_list_item_relations').fetchall()
        assert len(master_list_item_relations) == master_list_item_relation_count - len(affected_master_item_ids)
        master_details = db.execute('SELECT * FROM master_details').fetchall()
        assert len(master_details) == master_detail_count - len(affected_master_detail_ids)
        master_list_detail_relations = db.execute('SELECT * FROM master_list_detail_relations').fetchall()
        assert len(master_list_detail_relations) == master_list_detail_relation_count - len(affected_master_detail_ids)
        master_item_detail_relations = db.execute('SELECT * FROM master_item_detail_relations').fetchall()
        assert len(master_item_detail_relations) == master_item_detail_relation_count - len(affected_master_item_detail_relation_ids)
    # redirected to master_lists.index
    response = client.post("master-lists/2/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-lists/"
    # master list must exist
    response = client.post("master-lists/3/delete")
    assert response.status_code == 404


def test_new_master_item(app, client, auth):
    # user must be logged in
    response = client.get("/master-lists/1/master-items/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login('other', 'other')
    response = client.get("master-lists/1/master-items/new")
    assert response.status_code == 403
    # user must be admin
    auth.login('other', 'other')
    assert client.get('/master-lists/1/master-items/new').status_code == 403
    auth.login("admin2", "admin2")
    response = client.get('/master-lists/1/master-items/new')
    assert response.status_code == 200
    with app.app_context():
        # master list related detail names are served
        db = get_db()
        master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON d.id = r.master_detail_id'
            ' WHERE r.master_list_id = 1'
        ).fetchall()
        for master_detail in master_details:
            assert master_detail['name'].encode() in response.data
        # other master detail names are not served
        other_master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON d.id = r.master_detail_id'
            ' WHERE r.master_list_id <> 1'
        ).fetchall()
        for master_detail in other_master_details:
            assert master_detail['name'].encode() not in response.data
    # data validation
    response = client.post(
        '/master-lists/1/master-items/new', data={'name': '', '1': '', '2': ''}
    )
    assert b'Name is required' in response.data
    # new master item is saved to db correctly
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        master_items_before = db.execute(
            'SELECT id, creator_id, name FROM master_items'
        ).fetchall()
        master_details_before = db.execute(
            'SELECT d.id, d.name FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_list_id = 1'
        ).fetchall()
        master_item_detail_relations_before = db.execute(
            'SELECT id, master_item_id, master_detail_id, master_content'
            ' FROM master_item_detail_relations'
        ).fetchall()
        master_list_item_relations_before = db.execute(
            'SELECT id, master_list_id, master_item_id'
            ' FROM master_list_item_relations'
        ).fetchall()
        response = client.post(
            '/master-lists/1/master-items/new',
            data={
                'name': 'master item name 4',
                '1': 'master relation content 6',
                '2': 'master relation content 7',
            }
        )
        master_items_after = db.execute(
            'SELECT id, creator_id, name FROM master_items'
        ).fetchall()
        master_details_after = db.execute(
            'SELECT d.id, d.name FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_list_id = 1'
        ).fetchall()
        master_item_detail_relations_after = db.execute(
            'SELECT id, master_item_id, master_detail_id, master_content'
            ' FROM master_item_detail_relations'
        ).fetchall()
        master_list_item_relations_after = db.execute(
            'SELECT id, master_list_id, master_item_id'
            ' FROM master_list_item_relations'
        ).fetchall()
        assert master_items_after[:-1] == master_items_before
        assert master_details_after == master_details_before
        assert master_item_detail_relations_after[:-2] == master_item_detail_relations_before
        assert master_list_item_relations_after[:-1] == master_list_item_relations_before
        assert master_items_after[-1]['name'] == 'master item name 4'
        assert master_item_detail_relations_after[-2]['master_detail_id'] == 1
        assert master_item_detail_relations_after[-2]['master_content'] == 'master relation content 6'
        assert master_item_detail_relations_after[-1]['master_detail_id'] == 2
        assert master_item_detail_relations_after[-1]['master_content'] == 'master relation content 7'
        assert master_list_item_relations_after[-1]['master_list_id'] == 1
        assert master_list_item_relations_after[-1]['master_item_id'] == len(master_items_after)
        # redirect to master_list.view
        assert response.status_code == 302
        assert response.headers["Location"] == "/master-lists/1/view"


def test_view_master_item(client, auth, app):
    # user must be logged in
    response = client.get("/master-lists/1/master-items/1/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user doesn't need to be admin
    auth.login("other", "other")
    response = client.get("/master-lists/1/master-items/1/view")
    assert response.status_code == 200
    with app.app_context():
        # master item data gets served
        db = get_db()
        master_item = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id = 1'
        ).fetchone()
        master_contents = db.execute(
            'SELECT r.master_content, d.name AS master_detail_name'
            ' FROM master_item_detail_relations r'
            ' JOIN master_details d ON r.master_detail_id = d.id'
            ' WHERE r.master_item_id = 1'
        ).fetchall()
        assert str(master_item['id']).encode() in response.data
        assert master_item['name'].encode() in response.data
        for master_content in master_contents:
            assert master_content['master_content'].encode() in response.data
            assert master_content['master_detail_name'].encode() in response.data
        # other master item data does not get served
        other_master_items = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id <> 1'
        ).fetchall()
        for other_master_item in other_master_items:
            assert other_master_item['name'].encode() not in response.data
        other_master_contents = db.execute(
            'SELECT r.master_content'
            ' FROM master_item_detail_relations r'
            ' WHERE r.master_item_id <> 1'
        ).fetchall()
        for other_master_content in other_master_contents:
            assert other_master_content['master_content'].encode() not in response.data
        other_master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_list_id <> 1'
        ).fetchall()
        for other_master_detail in other_master_details:
            assert other_master_detail['name'].encode() not in response.data
    # master item must exist
    assert client.get('master-lists/1/master-items/4/view').status_code == 404


def test_edit_master_item(client, auth, app):
    # user must be logged in
    response = client.get("master-lists/1/master-items/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-lists/1/master-items/1/edit")
    assert response.status_code == 403
    auth.login("admin2", "admin2")
    response = client.get('master-lists/1/master-items/1/edit')
    assert response.status_code == 200
    with app.app_context():
        # item data gets served
        db = get_db()
        master_list = db.execute(
            'SELECT name, description'
            ' FROM master_lists'
            ' WHERE id = 1'
        ).fetchone()
        master_item = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id = 1'
        ).fetchone()
        master_contents = db.execute(
            'SELECT r.master_content, d.name AS master_detail_name'
            ' FROM master_item_detail_relations r'
            ' JOIN master_details d ON r.master_detail_id = d.id'
            ' WHERE r.master_item_id = 1'
        ).fetchall()
        assert master_list['name'].encode() in response.data
        assert master_list['description'].encode() in response.data
        assert str(master_item['id']).encode() in response.data
        assert master_item['name'].encode() in response.data
        for master_content in master_contents:
            assert master_content['master_content'].encode() in response.data
            assert master_content['master_detail_name'].encode() in response.data
        # other master item data does not get served
        other_master_lists = db.execute(
            'SELECT name, description'
            ' FROM master_lists'
            ' WHERE id <> 1'
        ).fetchall()
        for other_master_list in other_master_lists:
            assert other_master_list['name'].encode() not in response.data
            assert other_master_list['description'].encode() not in response.data
        other_master_items = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id <> 1'
        ).fetchall()
        for other_master_item in other_master_items:
            assert other_master_item['name'].encode() not in response.data
        other_master_contents = db.execute(
            'SELECT r.master_content'
            ' FROM master_item_detail_relations r'
            ' WHERE r.master_item_id <> 1'
        ).fetchall()
        for other_master_content in other_master_contents:
            assert other_master_content['master_content'].encode() not in response.data
        other_master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_list_id <> 1'
        ).fetchall()
        for other_master_detail in other_master_details:
            assert other_master_detail['name'].encode() not in response.data
    # data validation
    response = client.post(
        'master-lists/1/master-items/1/edit',
        data={
            'name': '',
            '1': '',
            '2': ''
        }
    )
    assert b'Name is required' in response.data
    with app.app_context():
        # changes are saved to database
        db = get_db()
        db.row_factory = dict_factory
        master_items_before = db.execute('SELECT name FROM master_items').fetchall()
        master_relations_before = db.execute('SELECT master_content FROM master_item_detail_relations').fetchall()
        response = client.post(
            'master-lists/1/master-items/1/edit',
            data={
                'name': 'master item name 1 updated',
                '1': 'master relation content 1 updated',
                '2': 'master relation content 2 updated'
            }
        )
        master_items_after = db.execute('SELECT name FROM master_items').fetchall()
        master_relations_after = db.execute('SELECT master_content FROM master_item_detail_relations').fetchall()
        assert master_items_after[0]['name'] == 'master item name 1 updated'
        assert master_relations_after[0]['master_content'] == 'master relation content 1 updated'
        assert master_relations_after[1]['master_content'] == 'master relation content 2 updated'
        # other master items and master relations are unchanged
        assert master_items_after[1:] == master_items_before[1:]
        assert master_relations_after[2:] == master_relations_before[2:]
    # redirected to master_lists.view
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-lists/1/view"
    # master item must exist
    assert client.get("master-lists/1/master-items/4/edit").status_code == 404


def test_delete_master_item(client, auth, app):
    # user must be logged in
    response = client.post('/master-lists/1/master-items/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be admin
    auth.login("other", "other")
    response = client.post("master-lists/1/master-items/1/delete")
    assert response.status_code == 403
    auth.login("admin2", "admin2")
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        master_items_before = db.execute('SELECT id, name FROM master_items').fetchall()
        master_contents_before = db.execute('SELECT master_content FROM master_item_detail_relations').fetchall()
        master_relations_before = db.execute('SELECT master_list_id, master_item_id FROM master_list_item_relations').fetchall()
        response = client.post("/master-lists/1/master-items/1/delete")
        master_items_after = db.execute("SELECT id, name FROM master_items").fetchall()
        master_contents_after = db.execute("SELECT master_content FROM master_item_detail_relations").fetchall()
        master_relations_after = db.execute('SELECT master_list_id, master_item_id FROM master_list_item_relations').fetchall()
        # only the affected master item gets deleted
        assert master_items_after == master_items_before[1:]
        # only the affected master detail relations get deleted
        assert master_contents_after == master_contents_before[2:]
        # only the affected master relation gets deleted
        assert master_relations_after == master_relations_before[1:]
    # redirected to master list
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-lists/1/view"
    # master item must exist
    response = client.post("master-lists/1/master-items/4/delete")
    assert response.status_code == 404


def test_new_master_detail(client, auth, app):
    # user must be logged in
    response = client.get("/master-lists/1/master-details/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-lists/1/master-details/new")
    assert response.status_code == 403
    auth.login("admin2", "admin2")
    response = client.get('/master-lists/1/master-details/new')
    assert response.status_code == 200
    # data validation
    response = client.post("/master-lists/1/master-details/new",
        data={"name": "", "description": ""}
    )
    assert b"Name is required" in response.data
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        master_details_before = db.execute("SELECT * FROM master_details").fetchall()
        master_list_detail_relations_before = db.execute('SELECT * FROM master_list_detail_relations').fetchall()
        response = client.post("/master-lists/1/master-details/new",
            data={
                "name": "master detail name 4",
                "description": "master detail description 4"
            }
        )
        master_details_after = db.execute('SELECT * FROM master_details').fetchall()
        master_list_detail_relations_after = db.execute('SELECT * FROM master_list_detail_relations').fetchall()
        assert master_details_after[-1]['name'] == 'master detail name 4'
        assert master_details_after[-1]['description'] == 'master detail description 4'
        assert master_details_after[:-1] == master_details_before
        assert master_list_detail_relations_after[:-1] == master_list_detail_relations_before
        assert master_list_detail_relations_after[-1]['master_list_id'] == 1
        master_details = db.execute(
            'SELECT name FROM master_details d'
            ' JOIN master_list_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_list_id = 1'
        ).fetchall()
        assert master_details[-1]["name"] == "master detail name 4"
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-lists/1/view"


def test_edit_master_detail(client, auth, app):
    # user must be logged in
    response = client.get("/master-lists/1/master-details/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("/master-lists/1/master-details/1/edit")
    assert response.status_code == 403
    auth.login("admin2", "admin2")
    response = client.get("/master-lists/1/master-details/1/edit")
    assert response.status_code == 200
    # master detail must exist
    response = client.get("/master-lists/1/master-details/4/edit")
    assert response.status_code == 404
    # data validation
    response = client.post(
        '/master-lists/1/master-details/1/edit',
        data={'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    with app.app_context():
        # master detail is updated in db
        db = get_db()
        db.row_factory = dict_factory
        master_details_before = db.execute("SELECT * FROM master_details").fetchall()
        master_list_detail_relations_before = db.execute("SELECT * FROM master_list_detail_relations").fetchall()
        master_item_detail_relations_before = db.execute("SELECT * FROM master_item_detail_relations").fetchall()
        response = client.post(
            "/master-lists/1/master-details/1/edit",
            data={
                "name": "master detail name 1 updated",
                "description": "master detail description 1 updated"
            }
        )
        master_details_after = db.execute("SELECT * FROM master_details").fetchall()
        master_list_detail_relations_after = db.execute("SELECT * FROM master_list_detail_relations").fetchall()
        master_item_detail_relations_after = db.execute("SELECT * FROM master_item_detail_relations").fetchall()
        assert master_details_after[1:] == master_details_before[1:]
        assert master_details_after[0] != master_details_before[0]
        assert master_details_after[0]['name'] == 'master detail name 1 updated'
        assert master_details_after[0]['description'] == 'master detail description 1 updated'
        assert master_list_detail_relations_before == master_list_detail_relations_after
        assert master_item_detail_relations_before == master_item_detail_relations_after
    # redirect to master list view
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-lists/1/view"


def test_delete_master_detail(client, auth, app):
    # user must be logged in
    response = client.post("/master-lists/1/master-details/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.post("/master-lists/1/master-details/1/delete")
    assert response.status_code == 403
    # master detail must exist
    auth.login("admin2", "admin2")
    response = client.post("/master-lists/1/master-details/4/delete")
    assert response.status_code == 404
    with app.app_context():
        # master detail and master relation records get deleted
        db = get_db()
        db.row_factory = dict_factory
        master_details_before = db.execute("SELECT * FROM master_details").fetchall()
        master_item_detail_relations_before = db.execute("SELECT * FROM master_item_detail_relations").fetchall()
        master_list_detail_relations_before = db.execute("SELECT * FROM master_list_detail_relations").fetchall()
        response = client.post("/master-lists/1/master-details/1/delete")
        master_details_after = db.execute("SELECT * FROM master_details").fetchall()
        master_item_detail_relations_after = db.execute("SELECT * FROM master_item_detail_relations").fetchall()
        master_list_detail_relations_after = db.execute("SELECT * FROM master_list_detail_relations").fetchall()
        assert master_details_before[1:] == master_details_after
        assert len(master_item_detail_relations_before) == len(master_item_detail_relations_after) + 2
        for master_item_detail_relation in master_item_detail_relations_after:
            assert master_item_detail_relation["master_detail_id"] != 1
        assert master_list_detail_relations_before[1:] == master_list_detail_relations_after
    # redirect to master view
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-lists/1/view"


