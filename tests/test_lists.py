import pytest
from incontext.db import get_db, dict_factory
from tests.test_db import get_other_tables

def test_index(client, auth, app):
    # user must be logged in
    response = client.get("/lists/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    with app.app_context():
        # Get data before the request
        data_before = get_other_tables()
        # Make the request
        auth.login()
        response = client.get("/lists/")
        assert response.status_code == 200
        # Get data after the request
        data_after = get_other_tables()
        # Assert the data hasn't changed
        assert data_after == data_before
        # The user's list data gets served while other users' data does not.
        db = get_db()
        lists = db.execute("SELECT * FROM lists").fetchall()
        for alist in lists:
            if alist["creator_id"] == 2:
                assert alist["name"].encode() in response.data
                assert alist["description"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data
                assert alist["description"].encode() not in response.data


def test_new(app, client, auth):
    # Get requests
    # User must be logged in
    response = client.get("/lists/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/lists/new")
    assert response.status_code == 200
    # Post requests
    # Data validation
    data = {"name": "", "description": ""}
    response = client.post("lists/new", data=data)
    assert b"Name is required" in response.data
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        # Get the affected tables before
        lists_before = db.execute("SELECT * FROM lists WHERE creator_id = 2").fetchall()
        # Get the other tables before
        other_tables_before = get_other_tables(["lists"])
        # Make the request
        data = {"name": "new list name", "description": "new list description"}
        response = client.post("lists/new", data=data)
        # Get the affected tables after
        lists_after = db.execute("SELECT * FROM lists WHERE creator_id = 2").fetchall()
        # Get the other tables after
        other_tables_after = get_other_tables(["lists"])
        # Assert the new rows are in the affected tables after
        new_list = next((alist for alist in lists_after if alist["name"] == "new list name"), None)
        assert new_list is not None
        # Assert that all other rows in the affected tables after comprise the affected tables before
        other_rows = [alist for alist in lists_after if alist["id"] != new_list["id"]]
        assert other_rows == lists_before
        # Assert that the other tables after is equal to the other tables before
        assert other_tables_after == other_tables_before
    # Redirect to lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/lists/"


def test_view(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("lists/1/view")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access
        auth.login("other", "other")
        assert client.get("lists/1/view").status_code == 403
        assert get_other_tables() == all_tables_before
        # The list must exist
        auth.login()
        assert client.get("lists/bogus/view").status_code == 404
        assert get_other_tables() == all_tables_before
        # Make the request
        response = client.get("/lists/1/view")
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before
        # List data gets served and other list data doesn't get served
        db = get_db()
        lists = db.execute("SELECT * FROM lists").fetchall()
        for alist in lists:
            if alist["id"] == 1:
                assert alist["name"].encode() in response.data
                assert alist["description"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data
                assert alist["description"].encode() not in response.data
        list_item_relations = db.execute(
            "SELECT i.name, r.list_id FROM items i"
            " JOIN list_item_relations r"
            " ON r.item_id = i.id"
        ).fetchall()
        for lir in list_item_relations:
            if lir["list_id"] == 1:
                assert lir["name"].encode() in response.data
            else:
                assert lir["name"].encode() not in response.data
        list_detail_relations = db.execute(
            "SELECT d.name, d.description, ldr.list_id FROM details d"
            " JOIN list_detail_relations ldr ON ldr.detail_id = d.id"
        ).fetchall()
        for ldr in list_detail_relations:
            if ldr["list_id"] == 1:
                assert ldr["name"].encode() in response.data
                assert ldr["description"].encode() in response.data
            else:
                assert ldr["name"].encode() not in response.data
                assert ldr["description"].encode() not in response.data
        item_detail_relations = db.execute(
            "SELECT idr.content, lir.list_id"
            " FROM item_detail_relations idr"
            " JOIN list_item_relations lir ON lir.item_id = idr.item_id"
        ).fetchall()
        for idr in item_detail_relations:
            if idr["list_id"] == 1:
                assert idr["content"].encode() in response.data
            else:
                assert idr["content"].encode() not in response.data
        contexts = db.execute(
            "SELECT c.name, c.description, r.list_id FROM contexts c"
            " JOIN context_list_relations r ON r.context_id = c.id"
        ).fetchall()
        context_names = []
        context_descriptions = []
        for context in contexts:
            if context["list_id"] == 1:
                context_names.append(context["name"])
                assert context["name"].encode() in response.data
                context_descriptions.append(context["description"])
                assert context["description"].encode() in response.data
            else:
                if context["name"] not in context_names:
                    assert context["name"] not in response.data
                if context["description"] not in context_descriptions:
                    assert context["description"] not in response.data


def test_edit(app, client, auth):
    # Get requests
    # User must be logged in
    response = client.get("/lists/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # User must be list creator
    auth.login("other", "other")
    assert client.get("lists/1/edit").status_code == 403
    auth.login()
    response = client.get("lists/1/edit")
    assert response.status_code == 200
    # List data gets served, other list data not served.
    with app.app_context():
        db = get_db()
        lists = db.execute("SELECT * FROM lists").fetchall()
        for alist in lists:
            if alist["id"] == 1:
                assert alist["name"].encode() in response.data
                assert alist["description"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data
                assert alist["description"].encode() not in response.data
    # Data validation
    response = client.post("lists/1/edit", data={"name": "", "description": ""})
    assert b"Name is required" in response.data
    # Changes are saved to database
    response = client.post(
        "lists/1/edit",
        data={"name": "item name 1 updated", "description": "item description 1 updated"}
    )
    with app.app_context():
        db = get_db()
        lists = db.execute("SELECT name, description FROM lists").fetchall()
        assert lists[0]["name"] == "item name 1 updated"
        assert lists[0]["description"] == "item description 1 updated"
        # Other lists are not changed
        for alist in lists[1:]:
            assert alist["name"] != "list name 1 updated"
            assert alist["description"] != "list description 1 updated"
    # Redirected to lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/lists/"
    # List must exist
    assert client.get("/lists/bogus/edit").status_code == 404


def test_delete(app, client, auth):
    # User must be logged in
    response = client.post("/lists/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # User must be list creator
    auth.login("other", "other")
    assert client.post("lists/1/delete").status_code == 403
    # List gets deleted
    auth.login()
    with app.app_context():
        db = get_db()
        # Get the affected tables before the request
        lists_before = db.execute("SELECT * FROM lists").fetchall()
        list_item_relations_before = db.execute("SELECT * FROM list_item_relations").fetchall()
        items_before = db.execute("SELECT * FROM items").fetchall()
        list_detail_relations_before = db.execute("SELECT * FROM list_detail_relations").fetchall()
        details_before = db.execute("SELECT * FROM details").fetchall()
        item_detail_relations_before = db.execute("SELECT * FROM item_detail_relations").fetchall()
        # Get the affected ids for each affected table
        affected_list_ids = [lb["id"] for lb in lists_before if lb["id"] == 1]
        affected_lir_ids = [lirb["id"] for lirb in list_item_relations_before if lirb["list_id"] == 1]
        affected_item_ids = [lirb["item_id"] for lirb in list_item_relations_before if lirb["list_id"] == 1]
        affected_ldr_ids = [ldrb["id"] for ldrb in list_detail_relations_before if ldrb["list_id"] == 1]
        affected_detail_ids = [ldrb["detail_id"] for ldrb in list_detail_relations_before if ldrb["list_id"] == 1]
        affected_idr_ids = [idr["id"] for idr in item_detail_relations_before if idr["item_id"] in affected_item_ids]
        # Get the other tables before the request
        other_tables_before = get_other_tables(["lists", "list_item_relations", "items", "list_detail_relations", "details", "item_detail_relations"])
        # Make the request
        response = client.post("/lists/1/delete")
        # Get the affected tables after the request
        lists_after = db.execute("SELECT * FROM lists").fetchall()
        items_after = db.execute("SELECT * FROM items").fetchall()
        details_after = db.execute("SELECT * FROM details").fetchall()
        list_item_relations_after = db.execute("SELECT * FROM list_item_relations").fetchall()
        list_detail_relations_after = db.execute("SELECT * FROM list_detail_relations").fetchall()
        item_detail_relations_after = db.execute("SELECT * FROM item_detail_relations").fetchall()
        # Assert the affected ids aren't in the tables after.
        for alist in lists_after:
            assert alist["id"] not in affected_list_ids
        for item in items_after:
            assert item["id"] not in affected_item_ids
        for detail in details_after:
            assert detail["id"] not in affected_detail_ids
        for lir in list_item_relations_after:
            assert lir["id"] not in affected_lir_ids
        for ldr in list_detail_relations_after:
            assert ldr["id"] not in affected_ldr_ids
        for idr in item_detail_relations_after:
            assert idr["id"] not in affected_idr_ids
        # Assert the number of rows has reduced by the right amount
        assert len(lists_before) - len(lists_after) == len(affected_list_ids)
        assert len(items_before) - len(items_after) == len(affected_item_ids)
        assert len(details_before) - len(details_after) == len(affected_detail_ids)
        assert len (list_item_relations_before) - len(list_item_relations_after) == len(affected_lir_ids)
        assert len (list_detail_relations_before) - len(list_detail_relations_after) == len(affected_ldr_ids)
        assert len (item_detail_relations_before) - len(item_detail_relations_after) == len(affected_idr_ids)
        # Assert other tables have not changed.
        other_tables_after = get_other_tables(["lists", "list_item_relations", "items", "list_detail_relations", "details", "item_detail_relations"])
        assert other_tables_before == other_tables_after
    # Redirected to lists.index
    response = client.post("lists/2/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/lists/"


def test_new_item(app, client, auth):
    # Get requests
    # User must be logged in
    response = client.get("/lists/1/items/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # User must be list creator
    auth.login("other", "other")
    assert client.get("/lists/1/items/new").status_code == 403
    with app.app_context():
        # Data is unchanged
        data_before = get_other_tables()
        # Make request
        auth.login()
        response = client.get("/lists/1/items/new")
        assert response.status_code == 200
        data_after = get_other_tables()
        assert data_after == data_before
        # List name and description are served while other list names and descriptions are not
        db = get_db()
        db.row_factory = dict_factory
        lists = db.execute("SELECT * FROM lists").fetchall()
        for alist in lists:
            if alist["id"] == 1:
                assert alist["name"].encode() in response.data
                assert alist["description"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data
                assert alist["description"].encode() not in response.data
        # List-related detail names are served while others are not
        list_details = db.execute(
            "SELECT d.name, r.list_id"
            " FROM details d JOIN list_detail_relations r"
            " ON d.id = r.detail_id"
        ).fetchall()
        for detail in list_details:
            if detail["list_id"] == 1:
                assert detail['name'].encode() in response.data
            else:
                assert detail['name'].encode() not in response.data
    # Post requests
    # Data validation
    data={"name": "", "1": "", "2": ""}
    response = client.post("/lists/1/items/new", data=data)
    assert b"Name is required" in response.data
    # New item is saved to db correctly
    with app.app_context():
        # Get the affected tables before the request
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute("SELECT * FROM items").fetchall()
        list_item_relations_before = db.execute("SELECT * FROM list_item_relations").fetchall()
        item_detail_relations_before = db.execute("SELECT * FROM item_detail_relations").fetchall()
        # Get the other tables before the request
        other_tables_before = get_other_tables(["items", "list_item_relations", "item_detail_relations"])
        # Make the request
        data={"name": "new item name", "1": "new content 1", "2": "new content 2"}
        response = client.post("/lists/1/items/new", data=data)
        # Get the affected tables after
        items_after = db.execute("SELECT * FROM items").fetchall()
        list_item_relations_after = db.execute("SELECT * FROM list_item_relations").fetchall()
        item_detail_relations_after = db.execute("SELECT * FROM item_detail_relations").fetchall()
        # Get the other tables after
        other_tables_after = get_other_tables(["items", "list_item_relations", "item_detail_relations"])
        # Assert that the other tables after equal the other tables before
        assert other_tables_after == other_tables_before
        # Assert the new rows are in the affected tables after
        new_item = [item for item in items_after if item["name"] == "new item name"]
        assert len(new_item) == 1
        new_item_id = new_item[0]["id"]
        new_list_item_relation = [lir for lir in list_item_relations_after if lir["list_id"] == 1 and lir["item_id"] == new_item_id]
        assert len (new_list_item_relation) == 1
        new_item_detail_relations = [idr for idr in item_detail_relations_after if idr["item_id"] == new_item_id]
        assert len(new_item_detail_relations) == 2
        for i, r in enumerate(new_item_detail_relations):
            assert r["content"] == f"new content {i + 1}"
        # Assert that all the other rows in the affected tables after comprise the affected tables before
        other_items = [item for item in items_after if item["id"] != new_item_id]
        assert other_items == items_before
        other_list_item_relations = [lir for lir in list_item_relations_after if lir["item_id"] != new_item_id]
        assert other_list_item_relations == list_item_relations_before
        other_item_detail_relations = [idr for idr in item_detail_relations_after if idr["item_id"] != new_item_id]
        assert other_item_detail_relations == item_detail_relations_before
        # redirect to list.view
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/1/view"


def test_view_item(client, auth, app):
    # Get requests
    # User must be logged in
    response = client.get("/lists/1/items/1/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # User must be list owner
    auth.login("other", "other")
    assert client.get("/lists/1/items/1/view").status_code == 403
    with app.app_context():
        # Data does not change
        # Get all tables before
        all_tables_before = get_other_tables()
        # Make request(s)
        auth.login()
        response = client.get("/lists/1/items/1/view")
        assert response.status_code == 200
        # Get all tables after
        all_tables_after = get_other_tables()
        # Assert data didn't change
        assert all_tables_after == all_tables_before
        # Get data to view
        db = get_db()
        db.row_factory = dict_factory
        relations = db.execute(
            "SELECT r.item_id, r.detail_id, r.content, i.name AS item_name, d.name AS detail_name, d.description AS detail_description"
            " FROM item_detail_relations r"
            " JOIN items i ON i.id = r.item_id"
            " JOIN details d ON d.id = r.detail_id"
        ).fetchall()
        # Assert the right data is served and the wrong data is not served
        item_names_right = [r["item_name"] for r in relations if r["item_id"] == 1]
        item_names_wrong = [r["item_name"] for r in relations if r["item_name"] not in item_names_right]
        detail_names_right = [r["detail_name"] for r in relations if r["item_id"] == 1]
        detail_names_wrong = [r["detail_name"] for r in relations if r["detail_name"] not in detail_names_right]
        content_right = [r["content"] for r in relations if r["item_id"] == 1]
        content_wrong = [r["content"] for r in relations if r["content"] not in content_right]
        rights = item_names_right + detail_names_right + content_right
        wrongs = item_names_wrong + detail_names_wrong + content_wrong
        for r in rights:
            assert r.encode() in response.data
        for w in wrongs:
            assert w.encode() not in response.data
    # item must exist
    assert client.get("lists/1/items/bogus/view").status_code == 404


def test_edit_item_get(client, auth, app):
    # User must be logged in and have access to item
    response = client.get("lists/1/items/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login('other', 'other')
    assert client.get("lists/1/items/1/edit").status_code == 403
    with app.app_context():
        # Data doesn't change
        all_tables = get_other_tables()
        auth.login()
        response = client.get('lists/1/items/1/edit')
        assert response.status_code == 200
        all_tables_after = get_other_tables()
        assert all_tables_after == get_other_tables()
        # List name and description are shown
        db = get_db()
        db.row_factory = dict_factory
        lists = db.execute("SELECT * FROM lists").fetchall()
        for alist in lists:
            if alist["id"] == 1:
                assert alist["name"].encode() in response.data
                assert alist["description"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data
                assert alist["description"].encode() not in response.data
        # List name, description, item name, detail names, contents all served, other data not served
        # Get data to view
        relations = db.execute(
            "SELECT r.item_id, r.detail_id, r.content, i.name AS item_name, d.name AS detail_name, d.description AS detail_description"
            " FROM item_detail_relations r"
            " JOIN items i ON i.id = r.item_id"
            " JOIN details d ON d.id = r.detail_id"
        ).fetchall()
        # Assert the right data is served and the wrong data is not served
        item_names_right = [r["item_name"] for r in relations if r["item_id"] == 1]
        item_names_wrong = [r["item_name"] for r in relations if r["item_name"] not in item_names_right]
        detail_names_right = [r["detail_name"] for r in relations if r["item_id"] == 1]
        detail_names_wrong = [r["detail_name"] for r in relations if r["detail_name"] not in detail_names_right]
        content_right = [r["content"] for r in relations if r["item_id"] == 1]
        content_wrong = [r["content"] for r in relations if r["content"] not in content_right]
        rights = item_names_right + detail_names_right + content_right
        wrongs = item_names_wrong + detail_names_wrong + content_wrong
        for r in rights:
            assert r.encode() in response.data
        for w in wrongs:
            assert w.encode() not in response.data
    # Item must exist
    assert client.get("lists/1/items/bogus/edit").status_code == 404
   

def test_edit_item_post(client, auth, app):
    with app.app_context():
        # Get data before
        all_tables_before = get_other_tables()
        # User must be logged in and have access to the item
        path = "/lists/1/items/1/edit"
        data = {"name": "", "1": "", "2":""}
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data hasn't changed
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        # Data hasn't changed
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Data validation
        auth.login()
        response = client.post(path, data=data)
        assert b"Name is required" in response.data
        # Data hasn't changed
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Item name and contents are updated, other data remains unchanged
        # Get data before
        db = get_db()
        db.row_factory = dict_factory
        relations_before = db.execute(
            "SELECT r.item_id, r.detail_id, r.content, i.name AS item_name, d.name AS detail_name, d.description AS detail_description"
            " FROM item_detail_relations r"
            " JOIN items i ON i.id = r.item_id"
            " JOIN details d ON d.id = r.detail_id"
        ).fetchall()
        other_tables_before = get_other_tables(["item_detail_relations", "items", "details"])
        # Make the request
        data={"name": "item name 1 updated", "1": "relation content 1 updated", "2": "relation content 2 updated"}
        response = client.post(path, data=data)
        relations_after = db.execute(
            "SELECT r.item_id, r.detail_id, r.content, i.name AS item_name, d.name AS detail_name, d.description AS detail_description"
            " FROM item_detail_relations r"
            " JOIN items i ON i.id = r.item_id"
            " JOIN details d ON d.id = r.detail_id"
        ).fetchall()
        other_tables_after = get_other_tables(["item_detail_relations", "items", "details"])
        # Right data has been updated while wrong data has not
        for i, r in enumerate(relations_after):
            if r["item_id"] == 1:
                assert r["item_name"] == "item name 1 updated"
                assert r["item_id"] == relations_before[i]["item_id"]
                assert r["detail_id"] == relations_before[i]["detail_id"]
                assert r["detail_description"] == relations_before[i]["detail_description"]
                if r["detail_id"] == 1:
                    assert r["content"] == "relation content 1 updated"
                elif r["detail_id"] == 2:
                    assert r["content"] == "relation content 2 updated"
                else:
                    raise Exception("Unexpected detail id")
            else:
                assert r == relations_before[i]
    # Redirected to lists.view
    assert response.status_code == 302
    assert response.headers["Location"] == "/lists/1/view"
    # Item must exist
    assert client.get("lists/1/items/bogus/edit").status_code == 404


def test_delete_item(client, auth, app):
    with app.app_context():
        # Get all data before
        all_tables_before = get_other_tables()
        # User must be logged in and have access to the item.
        response = client.post("/lists/1/items/1/delete")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data hasn't changed
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login("other", "other")
        assert client.post("/lists/1/items/1/delete").status_code == 403
        # Data hasn't changed
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Item gets deleted
        # Get the affected tables before the request
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute("SELECT * FROM items").fetchall()
        item_detail_relations_before = db.execute("SELECT * FROM item_detail_relations").fetchall()
        list_item_relations_before = db.execute("SELECT * FROM list_item_relations").fetchall()
        # Get the affected rows from the affected tables before the request
        affected_items = db.execute("SELECT * FROM items WHERE id = 1")
        affected_item_detail_relations = db.execute("SELECT * FROM item_detail_relations WHERE item_id = 1")
        affected_list_item_relations = db.execute("SELECT * FROM list_item_relations WHERE item_id = 1")
        # Get the other tables before the request
        other_tables_before = get_other_tables(["items", "item_detail_relations", "list_item_relations"])
        # Make the request
        auth.login()
        response = client.post("/lists/1/items/1/delete")
        # Get the affected tables after the request
        items_after = db.execute("SELECT * FROM items").fetchall()
        item_detail_relations_after = db.execute("SELECT * FROM item_detail_relations").fetchall()
        list_item_relations_after = db.execute("SELECT * FROM list_item_relations").fetchall()
        # Assert the affected rows aren't in the affected tables after
        for affected_item in affected_items:
            assert affected_item not in items_after
        for affected_item_detail_relation in affected_item_detail_relations:
            assert affected_item_detail_relation not in item_detail_relations_after
        for affected_list_item_relation in affected_list_item_relations:
            assert affected_list_item_relation not in list_item_relations_after
        # Assert the remaining rows are unchanged
        for item in items_after:
            assert item in items_before
        for idr in item_detail_relations_after:
            assert idr in item_detail_relations_before
        for lir in list_item_relations_after:
            assert lir in list_item_relations_before
        # Assert the other tables haven't changed
        other_tables_after = get_other_tables(["items", "item_detail_relations", "list_item_relations"])
        assert other_tables_after == other_tables_before
        # Redirected to list view
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/1/view"
        # Item must exist
        response = client.post("lists/1/items/bogus/delete")
        assert response.status_code == 404


def test_new_detail_get(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in and have access
        response = client.get("/lists/1/details/new")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login("other", "other")
        response = client.get("/lists/1/details/new")
        assert response.status_code == 403
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login()
        response = client.get("/lists/1/details/new")
        assert response.status_code == 200
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # List name is served and other list names aren't
        lists = get_db().execute("SELECT * FROM lists").fetchall()
        for alist in lists:
            if alist["id"] == 1:
                assert alist["name"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data


def test_new_detail_post(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in and have permission 
        path = "/lists/1/details/new"
        data = {"name": "", "description": ""}
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Data validation
        auth.login()
        response = client.post(path, data=data)
        assert b'Name is required' in response.data
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Make the request
        # Get affected tables before
        db = get_db()
        db.row_factory = dict_factory
        details_before = db.execute("SELECT * FROM details").fetchall()
        list_detail_relations_before = db.execute("SELECT * FROM list_detail_relations").fetchall()
        item_detail_relations_before = db.execute("SELECT * FROM item_detail_relations").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["details", "list_detail_relations", "item_detail_relations"])
        # Request
        data = {"name": "new detail name", "description": "new detail description"}
        response = client.post(path, data=data)
        # Get affected tables after
        details_after = db.execute("SELECT * FROM details").fetchall()
        list_detail_relations_after = db.execute("SELECT * FROM list_detail_relations").fetchall()
        item_detail_relations_after = db.execute("SELECT * FROM item_detail_relations").fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["details", "list_detail_relations", "item_detail_relations"])
        # Other tables are unchanged
        assert other_tables_after == other_tables_before
        # Affected tables after contain the rows of affected tables before
        for row in details_before:
            assert row in details_after
        for row in list_detail_relations_before:
            assert row in list_detail_relations_after
        for row in item_detail_relations_before:
            assert row in item_detail_relations_after
        # Affected tables after contains expected rows
        expected_rows = [row for row in details_after if row["name"] == "new detail name"]
        assert len(expected_rows) == 1
        new_detail_id = expected_rows[0]["id"]
        expected_rows = [row for row in list_detail_relations_after if row["detail_id"] == new_detail_id]
        assert len(expected_rows) == 1
        assert expected_rows[0]["list_id"] == 1
        expected_rows = [row for row in item_detail_relations_after if row["detail_id"] == new_detail_id]
        n = db.execute(
            "SELECT COUNT(*) AS count FROM items i JOIN list_item_relations lir"
            " ON lir.item_id = i.id WHERE lir.list_id = 1"
        ).fetchone()["count"]
        assert len(expected_rows) == n
        for row in expected_rows:
            assert row["content"] == ""
        # Redirected to list view
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/1/view"
        # List must exist
        all_tables_before = get_other_tables()
        response = client.post("lists/bogus/details/new", data=data)
        assert response.status_code == 404
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before


def test_edit_detail_get(client, auth, app):
    with app.app_context():
        all_tables_before = get_other_tables()
        path = "/lists/1/details/1/edit"
        # User must be logged in and have access to the list
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login("other", "other")
        response = client.post(path)
        assert response.status_code == 403 
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login()
        response = client.get(path)
        assert response.status_code == 200
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # List name and description are served while others aren't
        # Get data to view
        db = get_db()
        lists = db.execute("SELECT * FROM lists")
        details = db.execute("SELECT * FROM details")
        # Assert right data is served and wrong data isn't
        for alist in lists:
            if alist["id"] == 1:
                assert alist["name"].encode() in response.data
                assert alist["description"].encode() in response.data
            else:
                assert alist["name"].encode() not in response.data
                assert alist["description"].encode() not in response.data
        for detail in details:
            if detail["id"] == 1:
                assert detail["name"].encode() in response.data
                assert detail["description"].encode() in response.data
            else:
                assert detail["name"].encode() not in response.data
                assert detail["description"].encode() not in response.data
        # Detail must exist
        response = client.get("/lists/1/details/bogus/edit")
        assert response.status_code == 404
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        

def test_edit_detail_post(app, client, auth):
    with app.app_context():
        # Get data before
        all_tables_before = get_other_tables()
        # User must be logged in and have access to the list
        path = "/lists/1/details/1/edit"
        data = {"name": "", "description": ""}
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data is unchanged
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        # Data is unchanged
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Data validation
        auth.login()
        response = client.post(path, data=data)
        assert b'Name is required' in response.data
        # Data is unchanged
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Detail name and description are changed, and nothing else changes
        # Get affected tables before
        db = get_db()
        db.row_factory = dict_factory
        details_before = db.execute('SELECT * FROM details').fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["details"])
        # Make the request
        data = {"name": "detail name 1 updated", "description": "detail description 1 updated"}
        response = client.post(path, data=data)
        # Get affected tables after
        details_after = db.execute('SELECT * FROM details').fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["details"])
        # The right data has changed and the wrong data has not
        for detail in details_after:
            if detail["id"] == 1:
                detail not in details_before
                detail["name"] == "detail name 1 updated"
                detail["description"] == "detail 1 description updated"
            else:
                detail in details_before
        # Redirect to list view
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/1/view"
        # Detail must exist
        # Get all tables before
        all_tables_before = get_other_tables()
        response = client.post("/lists/1/details/bogus/edit")
        assert response.status_code == 404
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # List must exist
        response = client.post("/lists/bogus/details/1/edit")
        assert response.status_code == 404
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before


def test_delete_detail(client, auth, app):
    with app.app_context():
        # Get all data before
        all_tables_before = get_other_tables()
        # User must be logged in
        path = "/lists/1/details/1/delete"
        response = client.post(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # User must have access to the list
        auth.login("other", "other")
        response = client.post(path)
        assert response.status_code == 403
        # Detail must exist
        auth.login()
        response = client.post("/lists/1/details/bogus/delete")
        assert response.status_code == 404
        # List must exist
        response = client.post("/lists/bogus/details/1/delete")
        assert response.status_code == 404
        # Data didn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Detail and related records get deleted
        # Get affected tables before request
        db = get_db()
        db.row_factory = dict_factory
        details_before = db.execute('SELECT * FROM details').fetchall()
        list_detail_relations_before = db.execute('SELECT * FROM list_detail_relations').fetchall()
        item_detail_relations_before = db.execute('SELECT * FROM item_detail_relations').fetchall()
        # Get other tables before request
        other_tables_before = get_other_tables(["details", "list_detail_relations", "item_detail_relations"])
        # Make the request
        response = client.post(path)
        # Get affected tables after request
        details_after = db.execute('SELECT * FROM details').fetchall()
        list_detail_relations_after = db.execute('SELECT * FROM list_detail_relations').fetchall()
        item_detail_relations_after = db.execute('SELECT * FROM item_detail_relations').fetchall()
        # Get other tables after request
        other_tables_after = get_other_tables(["details", "list_detail_relations", "item_detail_relations"])
        # Other tables are unchanged
        assert other_tables_after == other_tables_before
        # Affected rows are not in the affected tables after and other rows are unaffected
        affected_details = [d for d in details_before if d["id"] == 1]
        affected_ldrs = [ldr for ldr in list_detail_relations_before if ldr["detail_id"] == 1]
        affected_idrs = [idr for idr in item_detail_relations_before if idr["detail_id"] == 1]
        for detail in details_after:
            assert detail not in affected_details
            assert detail in details_before
        for ldr in list_detail_relations_after:
            assert ldr not in affected_ldrs
            assert ldr in list_detail_relations_before
        for idr in item_detail_relations_after:
            assert idr not in affected_idrs
            assert idr in item_detail_relations_before
        assert len(details_after) == len(details_before) - len(affected_details)
        assert len(list_detail_relations_after) == len(list_detail_relations_before) - len(affected_ldrs)
        assert len(item_detail_relations_after) == len(item_detail_relations_before) - len(affected_idrs)
        # Redirect to list view
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/1/view"
