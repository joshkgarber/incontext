import pytest
from incontext.db import get_db, dict_factory

def test_index(client, auth):
    # user must be logged in
    response = client.get('/lists/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    auth.login()
    response = client.get('/lists/')
    assert response.status_code == 200
    # test user's list data gets served
    assert b'list name 1' in response.data
    assert b'list description 1' in response.data
    assert b'list name 2' in response.data
    assert b'list description 2' in response.data
    # other user's list data does not get served
    assert b'list name 3' not in response.data
    assert b'list description 3' not in response.data
    assert b'list name 4' not in response.data
    assert b'list description 4' not in response.data


def test_new(app, client, auth):
    # user must be logged in
    response = client.get('/lists/new')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    auth.login()
    response = client.get('/lists/new')
    assert response.status_code == 200
    # data validation
    response = client.post(
        'lists/new',
        data = {'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    with app.app_context():
        # list is saved to database
        db = get_db()
        lists_before = db.execute("SELECT name, description FROM lists WHERE creator_id = 2").fetchall()
        response = client.post(
            'lists/new',
            data = {'name': 'new list name', 'description': 'new list description'},
        )
        lists_after = db.execute('SELECT name, description FROM lists WHERE creator_id = 2').fetchall()
        assert len(lists_after) == len(lists_before) + 1
        assert lists_after[-1]['name'] == 'new list name'
        assert lists_after[-1]['description'] == 'new list description'
    # redirected to lists.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/'


def test_view(app, client, auth):
    # user must be logged in
    response = client.get('lists/1/view')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be list creator
    auth.login('other', 'other')
    assert client.get('lists/1/view').status_code == 403
    auth.login()
    response = client.get('/lists/1/view')
    assert response.status_code == 200
    # list data gets served
    assert b'list name 1' in response.data
    assert b'list description 1' in response.data
    assert b'detail name 1' in response.data
    assert b'detail name 2' in response.data
    assert b'item name 1' in response.data
    assert b'item name 2' in response.data
    assert b'relation content 1' in response.data
    assert b'relation content 2' in response.data
    assert b'relation content 3' in response.data
    assert b'relation content 4' in response.data
    assert b'detail description 1' in response.data
    assert b'detail description 2' in response.data
    # other list data does not get served
    assert b'item name 3' not in response.data
    assert b'detail name 3' not in response.data
    assert b'relation content 5' not in response.data
    assert b'detail description 3' not in response.data
    # other users list data does not get served
    assert b'item name 4' not in response.data
    assert b'item name 5' not in response.data
    assert b'item name 6' not in response.data
    assert b'detail name 4' not in response.data
    assert b'detail name 5' not in response.data
    assert b'detail name 6' not in response.data
    assert b'relation content 5' not in response.data
    assert b'relation content 6' not in response.data
    assert b'relation content 7' not in response.data
    assert b'relation content 8' not in response.data
    assert b'relation content 9' not in response.data
    assert b'relation content 10' not in response.data
    assert b'detail description 4' not in response.data
    assert b'detail description 5' not in response.data
    assert b'detail description 6' not in response.data
    # list must exist
    assert client.get('lists/50/view').status_code == 404


def test_edit(app, client, auth):
    # user must be logged in
    response = client.get('/lists/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be list creator
    auth.login('other', 'other')
    assert client.get('lists/1/edit').status_code == 403
    auth.login()
    response = client.get('lists/1/edit')
    assert response.status_code == 200
    # list data gets served
    assert b'list name 1' in response.data
    assert b'list description 1' in response.data
    # data validation
    response = client.post('lists/1/edit', data={'name': '', 'description': ''})
    assert b'Name is required' in response.data
    # changes are saved to database
    response = client.post(
        'lists/1/edit',
        data={'name': 'item name 1 updated', 'description': 'item description 1 updated'}
    )
    with app.app_context():
        db = get_db()
        lists = db.execute('SELECT name, description FROM lists').fetchall()
        assert lists[0]['name'] == 'item name 1 updated'
        assert lists[0]['description'] == 'item description 1 updated'
        # other lists are not changed
        for list in lists[1:]:
            assert list['name'] != 'list name 1 updated'
            assert list['description'] != 'list description 1 updated'
    # redirected to lists.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/'
    # list must exist
    assert client.get('/lists/50/edit').status_code == 404


def test_delete(app, client, auth):
    # user must be logged in
    response = client.post('/lists/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be list creator
    auth.login('other', 'other')
    assert client.post('lists/1/delete').status_code == 403
    # list gets deleted
    auth.login()
    with app.app_context():
        db = get_db()
        item_count = db.execute(
            'SELECT COUNT(id) AS count FROM items'
        ).fetchone()['count']
        detail_count = db.execute(
            'SELECT COUNT(id) AS count FROM details'
        ).fetchone()['count']
        item_detail_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM item_detail_relations'
        ).fetchone()['count']
        list_count = db.execute(
            'SELECT COUNT(id) AS count FROM lists'
        ).fetchone()['count']
        list_item_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM list_item_relations'
        ).fetchone()['count']
        list_detail_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM list_detail_relations'
        ).fetchone()['count']
        affected_item_ids = db.execute(
            'SELECT item_id FROM list_item_relations WHERE list_id = 1'
        ).fetchall()
        assert len(affected_item_ids) == 2
        affected_item_ids = [item_id['item_id'] for item_id in affected_item_ids]
        placeholders_affected_item_ids = f'{"?, " * len(affected_item_ids)}'[:-2]
        affected_detail_ids = db.execute(
            'SELECT detail_id FROM list_detail_relations WHERE list_id = 1'
        ).fetchall()
        assert len(affected_detail_ids) == 2
        affected_detail_ids = [detail_id['detail_id'] for detail_id in affected_detail_ids]
        placeholders_affected_detail_ids = f'{"?, " * len(affected_detail_ids)}'[:-2]
        affected_item_and_detail_ids = affected_item_ids + affected_detail_ids
        affected_relation_ids = db.execute(
            'SELECT id, item_id FROM item_detail_relations'
            f' WHERE item_id IN ({placeholders_affected_item_ids})'
            f' OR detail_id IN ({placeholders_affected_detail_ids})',
            affected_item_and_detail_ids
        ).fetchall()
        assert len(affected_relation_ids) == 4
        response = client.post('/lists/1/delete')
        deleted_list = db.execute('SELECT * FROM lists WHERE id = 1').fetchone()
        assert deleted_list == None
        deleted_list_item_relations = db.execute(
            'SELECT * FROM list_item_relations WHERE list_id = 1'
        ).fetchall()
        assert len(deleted_list_item_relations) == 0
        deleted_list_detail_relations = db.execute('SELECT * FROM list_detail_relations WHERE list_id = 1').fetchall()
        assert len(deleted_list_detail_relations) == 0
        deleted_list_items = db.execute(
            f'SELECT * FROM items WHERE id IN ({placeholders_affected_item_ids})',
            affected_item_ids
        ).fetchall()
        assert len(deleted_list_items) == 0
        deleted_list_details = db.execute(
            f'SELECT * FROM details WHERE id IN ({placeholders_affected_detail_ids})',
            affected_detail_ids
        ).fetchall()
        assert len(deleted_list_details) == 0
        deleted_list_relations = db.execute(
            'SELECT * FROM item_detail_relations'
            f' WHERE item_id IN ({placeholders_affected_item_ids})'
            f' OR detail_id IN ({placeholders_affected_detail_ids})',
            affected_item_and_detail_ids
        ).fetchall()
        assert len(deleted_list_relations) == 0
        # other list data does not get deleted
        items = db.execute('SELECT * FROM items').fetchall()
        assert len(items) == item_count - len(affected_item_ids)
        details = db.execute('SELECT * FROM details').fetchall()
        assert len(details) == detail_count - len(affected_detail_ids)
        item_detail_relations = db.execute('SELECT * FROM item_detail_relations').fetchall()
        assert len(item_detail_relations) == item_detail_relation_count - len(affected_relation_ids)
        lists = db.execute('SELECT * FROM lists').fetchall()
        assert len(lists) == list_count - 1
        list_item_relations = db.execute('SELECT * FROM list_item_relations').fetchall()
        assert len(list_item_relations) == list_item_relation_count - len(affected_item_ids)
        list_detail_relations = db.execute('SELECT * FROM list_detail_relations').fetchall()
        assert len(list_detail_relations) == list_detail_relation_count - len(affected_detail_ids)
    # redirected to lists.index
    response = client.post('lists/2/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/'


def test_new_item(app, client, auth):
    # user must be logged in
    response = client.get('/lists/1/items/new')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be list creator
    auth.login('other', 'other')
    assert client.get('/lists/1/items/new').status_code == 403
    auth.login()
    response = client.get('/lists/1/items/new')
    assert response.status_code == 200
    # list-specific detail names are served
    with app.app_context():
        db = get_db()
        list_details = db.execute(
            'SELECT d.name'
            ' FROM details d'
            ' JOIN list_detail_relations r'
            ' ON d.id = r.detail_id'
            ' WHERE r.list_id = 1'
        ).fetchall()
        for detail in list_details:
            assert detail['name'].encode() in response.data
        # other detail names are not served
        other_list_details = db.execute(
            'SELECT d.name'
            ' FROM details d'
            ' JOIN list_detail_relations r'
            ' ON d.id = r.detail_id'
            ' WHERE r.list_id <> 1'
        ).fetchall()
        for detail in other_list_details:
            assert detail['name'].encode() not in response.data
    # data validationa
    response = client.post(
        '/lists/1/items/new', data={'name': '', '1': '', '2': ''}
    )
    assert b'Name is required' in response.data
    # new item is saved to db correctly
    with app.app_context():
        db = get_db()
        items_before = db.execute(
            'SELECT id, creator_id, name FROM items'
        ).fetchall()
        list_details_before = db.execute(
            'SELECT d.id, d.name FROM details d'
            ' JOIN list_detail_relations r'
            ' ON r.detail_id = d.id'
            ' WHERE r.list_id = 1'
        ).fetchall()
        item_detail_relations_before = db.execute(
            'SELECT id, item_id, detail_id, content'
            ' FROM item_detail_relations'
        ).fetchall()
        list_item_relations_before = db.execute(
            'SELECT id, list_id, item_id'
            ' FROM list_item_relations'
        ).fetchall()
        response = client.post(
            '/lists/1/items/new',
            data={
                'name': 'list item 7',
                '1': 'relation content 11',
                '2': 'relation content 12',
            }
        )
        items_after = db.execute(
            'SELECT id, creator_id, name FROM items'
        ).fetchall()
        list_details_after = db.execute(
            'SELECT d.id, d.name FROM details d'
            ' JOIN list_detail_relations r'
            ' ON r.detail_id = d.id'
            ' WHERE r.list_id = 1'
        ).fetchall()
        item_detail_relations_after = db.execute(
            'SELECT id, item_id, detail_id, content'
            ' FROM item_detail_relations'
        ).fetchall()
        list_item_relations_after = db.execute(
            'SELECT id, list_id, item_id'
            ' FROM list_item_relations'
        ).fetchall()
        assert items_after[:-1] == items_before
        assert list_details_after == list_details_before
        assert item_detail_relations_after[:-2] == item_detail_relations_before
        assert list_item_relations_after[:-1] == list_item_relations_before
        assert items_after[-1]['name'] == 'list item 7'
        assert item_detail_relations_after[-2]['detail_id'] == 1
        assert item_detail_relations_after[-2]['content'] == 'relation content 11'
        assert item_detail_relations_after[-1]['detail_id'] == 2
        assert item_detail_relations_after[-1]['content'] == 'relation content 12'
        assert list_item_relations_after[-1]['list_id'] == 1
        assert list_item_relations_after[-1]['item_id'] == len(items_after)
        # redirect to list.view
        assert response.status_code == 302
        assert response.headers['Location'] == '/lists/1/view'


def test_view_item(client, auth, app):
    # user must be logged in
    response = client.get('/lists/1/items/1/view')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be list owner
    auth.login('other', 'other')
    assert client.get('/lists/1/items/1/view').status_code == 403
    auth.login()
    response = client.get('/lists/1/items/1/view')
    assert response.status_code == 200
    # item data gets served
    with app.app_context():
        db = get_db()
        item = db.execute(
            'SELECT id, name'
            ' FROM items'
            ' WHERE id = 1'
        ).fetchone()
        contents = db.execute(
            'SELECT r.content, d.name AS detail_name'
            ' FROM item_detail_relations r'
            ' JOIN details d ON r.detail_id = d.id'
            ' WHERE r.item_id = 1'
        ).fetchall()
        assert str(item['id']).encode() in response.data
        assert item['name'].encode() in response.data
        for content in contents:
            assert content['content'].encode() in response.data
            assert content['detail_name'].encode() in response.data
        # other item data does not get served
        other_items = db.execute(
            'SELECT id, name'
            ' FROM items'
            ' WHERE id <> 1'
        ).fetchall()
        for other_item in other_items:
            assert other_item['name'].encode() not in response.data
        other_contents = db.execute(
            'SELECT r.content'
            ' FROM item_detail_relations r'
            ' WHERE r.item_id <> 1'
        ).fetchall()
        for other_content in other_contents:
            assert other_content['content'].encode() not in response.data
        other_details = db.execute(
            'SELECT d.name'
            ' FROM details d'
            ' JOIN list_detail_relations r'
            ' ON r.detail_id = d.id'
            ' WHERE r.list_id <> 1'
        ).fetchall()
        for other_detail in other_details:
            assert other_detail['name'].encode() not in response.data
    # item must exist
    assert client.get('lists/1/items/70/view').status_code == 404


def test_edit_item(client, auth, app):
    # user must be logged in
    response = client.get('lists/1/items/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have access to item
    auth.login('other', 'other')
    assert client.get('lists/1/items/1/edit').status_code == 403
    auth.login()
    response = client.get('lists/1/items/1/edit')
    assert response.status_code == 200
    # item data gets served
    with app.app_context():
        db = get_db()
        the_list = db.execute(
            'SELECT name, description'
            ' FROM lists'
            ' WHERE id = 1'
        ).fetchone()
        item = db.execute(
            'SELECT id, name'
            ' FROM items'
            ' WHERE id = 1'
        ).fetchone()
        contents = db.execute(
            'SELECT r.content, d.name AS detail_name'
            ' FROM item_detail_relations r'
            ' JOIN details d ON r.detail_id = d.id'
            ' WHERE r.item_id = 1'
        ).fetchall()
        assert the_list['name'].encode() in response.data
        assert the_list['description'].encode() in response.data
        assert str(item['id']).encode() in response.data
        assert item['name'].encode() in response.data
        for content in contents:
            assert content['content'].encode() in response.data
            assert content['detail_name'].encode() in response.data
        # other item data does not get served
        other_lists = db.execute(
            'SELECT name, description'
            ' FROM lists'
            ' WHERE id <> 1'
        ).fetchall()
        for other_list in other_lists:
            assert other_list['name'].encode() not in response.data
            assert other_list['description'].encode() not in response.data
        other_items = db.execute(
            'SELECT id, name'
            ' FROM items'
            ' WHERE id <> 1'
        ).fetchall()
        for other_item in other_items:
            assert other_item['name'].encode() not in response.data
        other_contents = db.execute(
            'SELECT r.content'
            ' FROM item_detail_relations r'
            ' WHERE r.item_id <> 1'
        ).fetchall()
        for other_content in other_contents:
            assert other_content['content'].encode() not in response.data
        other_details = db.execute(
            'SELECT d.name'
            ' FROM details d'
            ' JOIN list_detail_relations r'
            ' ON r.detail_id = d.id'
            ' WHERE r.list_id <> 1'
        ).fetchall()
        for other_detail in other_details:
            assert other_detail['name'].encode() not in response.data
    # data validation
    response = client.post(
        'lists/1/items/1/edit',
        data={
            'name': '',
            '1': '',
            '2': ''
        }
    )
    assert b'Name is required' in response.data
    # changes are saved to database
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute('SELECT name FROM items').fetchall()
        relations_before = db.execute('SELECT content FROM item_detail_relations').fetchall()
        response = client.post(
            'lists/1/items/1/edit',
            data={
                'name': 'item name 1 updated',
                '1': 'relation content 1 updated',
                '2': 'relation content 2 updated'
            }
        )
        items_after = db.execute('SELECT name FROM items').fetchall()
        relations_after = db.execute('SELECT content FROM item_detail_relations').fetchall()
        assert items_after[0]['name'] == 'item name 1 updated'
        assert relations_after[0]['content'] == 'relation content 1 updated'
        assert relations_after[1]['content'] == 'relation content 2 updated'
        # other items and relations are unchanged
        assert items_after[1:] == items_before[1:]
        assert relations_after[2:] == relations_before[2:]
    # redirected to lists.view
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/1/view'
    # item must exist
    assert client.get('lists/1/items/70/edit').status_code == 404


def test_delete_item(client, auth, app):
    # user must be logged in
    response = client.post('/lists/1/items/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have permission
    auth.login('other', 'other')
    assert client.post('/lists/1/items/1/delete').status_code == 403
    auth.login()
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute('SELECT id, name FROM items').fetchall()
        contents_before = db.execute('SELECT content FROM item_detail_relations').fetchall()
        relations_before = db.execute('SELECT list_id, item_id FROM list_item_relations').fetchall()
        response = client.post('/lists/1/items/1/delete')
        items_after = db.execute('SELECT id, name FROM items').fetchall()
        contents_after = db.execute('SELECT content FROM item_detail_relations').fetchall()
        relations_after = db.execute('SELECT list_id, item_id FROM list_item_relations').fetchall()
        # only the affected item gets deleted
        assert items_after == items_before[1:]
        # only the affected detail relations get deleted
        assert contents_after == contents_before[2:]
        # only the affected list relation gets deleted
        assert relations_after == relations_before[1:]
    # redirected to list
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/1/view'
    # item must exist
    response = client.post('lists/1/items/70/delete')
    assert response.status_code == 404


def test_new_detail(client, auth, app):
    # user must be logged in
    response = client.get('/lists/1/details/new')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    auth.login()
    response = client.get('/lists/1/details/new')
    assert response.status_code == 200
    # user must have permission
    auth.login('other', 'other')
    assert client.get('/lists/1/details/new').status_code == 403
    assert client.post('/lists/1/details/new').status_code == 403
    auth.login()
    response = client.get('/lists/1/details/new')
    assert response.status_code == 200
    # data validation
    response = client.post('/lists/1/details/new',
        data={'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        details_before = db.execute('SELECT * FROM details').fetchall()
        rels_before = db.execute('SELECT * FROM list_detail_relations').fetchall()
        response = client.post('/lists/1/details/new',
            data={
                'name': 'detail name 7',
                'description': 'detail description 7'
            }
        )
        details_after = db.execute('SELECT * FROM details').fetchall()
        rels_after = db.execute('SELECT * FROM list_detail_relations').fetchall()
        assert details_after[-1]['name'] == 'detail name 7'
        assert details_after[-1]['description'] == 'detail description 7'
        assert details_after[:-1] == details_before
        assert rels_after[:-1] == rels_before
        assert rels_after[-1]['list_id'] == 1
        details = db.execute(
            'SELECT name FROM details d'
            ' JOIN list_detail_relations r'
            ' ON r.detail_id = d.id'
            ' WHERE r.list_id = 1'
        ).fetchall()
        assert details[-1]['name'] == 'detail name 7'
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/1/view'


def test_edit_detail(client, auth, app):
    # user must be logged in
    response = client.get('/lists/1/details/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    response = client.post('lists/1/details/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have permission
    auth.login('other', 'other')
    response = client.get('/lists/1/details/1/edit')
    assert response.status_code == 403
    response = client.post('lists/1/details/1/edit')
    assert response.status_code == 403
    auth.login()
    response = client.get('/lists/1/details/1/edit')
    assert response.status_code == 200
    # detail must exist
    response = client.get('/lists/1/details/7/edit')
    assert response.status_code == 404
    # data validation
    response = client.post(
        '/lists/1/details/1/edit',
        data={'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    # detail is updated in db
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        details_before = db.execute('SELECT * FROM details').fetchall()
        rels_before = db.execute('SELECT * FROM list_detail_relations').fetchall()
        irels_before = db.execute('SELECT * FROM item_detail_relations').fetchall()
        response = client.post(
            '/lists/1/details/1/edit',
            data={
                'name': 'detail name 1 updated',
                'description': 'detail description 1 updated'
            }
        )
        details_after = db.execute('SELECT * FROM details').fetchall()
        rels_after = db.execute('SELECT * FROM list_detail_relations').fetchall()
        irels_after = db.execute('SELECT * FROM item_detail_relations').fetchall()
        assert details_after[1:] == details_before[1:]
        assert details_after[0] != details_before[0]
        assert details_after[0]['name'] == 'detail name 1 updated'
        assert details_after[0]['description'] == 'detail description 1 updated'
        assert rels_before == rels_after
        assert irels_before == irels_after
    # redirect to list view
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/1/view'


def test_delete_detail(client, auth, app):
    # user must be logged in
    response = client.post('/lists/1/details/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have permisstion
    auth.login('other', 'other')
    response = client.post('/lists/1/details/1/delete')
    assert response.status_code == 403
    # detail must exist
    auth.login()
    response = client.post('/lists/1/details/7/delete')
    assert response.status_code == 404
    # detail and related records get deleted
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        dets_before = db.execute('SELECT * FROM details').fetchall()
        i_d_rels_before = db.execute('SELECT * FROM item_detail_relations').fetchall()
        l_d_rels_before = db.execute('SELECT * FROM list_detail_relations').fetchall()
        response = client.post('/lists/1/details/1/delete')
        dets_after = db.execute('SELECT * FROM details').fetchall()
        i_d_rels_after = db.execute('SELECT * FROM item_detail_relations').fetchall()
        l_d_rels_after = db.execute('SELECT * FROM list_detail_relations').fetchall()
        assert dets_before[1:] == dets_after
        assert len(i_d_rels_before) == len(i_d_rels_after) + 2
        for rel in i_d_rels_after:
            assert rel['detail_id'] != 1
        assert l_d_rels_before[1:] == l_d_rels_after
    # redirect to list view
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists/1/view'
