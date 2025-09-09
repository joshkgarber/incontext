import pytest
from incontext.db import get_db, dict_factory
from incontext.master_lists import get_master_list

def test_new_tethered_list(app, client, auth):
    # Get requests
    # User must be logged in
    response = client.get("/lists/new-tethered")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/lists/new-tethered")
    assert response.status_code == 200
    # Page provides all master lists as options
    with app.app_context():
        master_list_ids = get_db().execute("SELECT id from master_lists")
        for master_list_id in master_list_ids:
            option =  f'<input type="hidden" name="master_list_id" value="{master_list_id["id"]}">'
            assert option.encode() in response.data
    # Post requests
    # User must be logged in
    auth.logout()
    response = client.post("/lists/new-tethered")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
# Master list id must exist
    auth.login()
    data = dict(name="tethered", master_list_id = 3) 
    response = client.post("/lists/new-tethered", data=data)
    assert response.status_code == 404
    # A new record is added to `lists` and `list_tethers`.
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        lists_before = db.execute("SELECT id FROM lists").fetchall()
        list_tethers_before = db.execute("SELECT id FROM list_tethers").fetchall()
        data = dict(name="tethered", description="", master_list_id=1)
        response = client.post("/lists/new-tethered", data=data)
        lists_after = db.execute("SELECT id FROM lists").fetchall()
        list_tethers_after = db.execute("SELECT id FROM list_tethers").fetchall()
        assert len(lists_after) == len(lists_before) + 1
        assert len(list_tethers_after) == len(list_tethers_before) + 1
        # Redirected to the lists's view view
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/8/view"


def test_view_tethered_list(app, client, auth):
    # User must be logged in and own the list
    response = client.get("/lists/5/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get("/lists/5/view")
    assert response.status_code == 403
    auth.login()
    response = client.get("/lists/5/view")
    assert response.status_code == 200
    # Showing data of the master list
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        master_list_id = db.execute("SELECT master_list_id FROM list_tethers WHERE list_id = 5").fetchone()["master_list_id"]
        other_master_list_ids = db.execute("SELECT id FROM master_lists WHERE id != ?", (master_list_id,)).fetchall()
        master_list = get_master_list(master_list_id, False)
        assert master_list["name"].encode() in response.data
        assert master_list["description"].encode() in response.data
        master_items = master_list["master_items"]
        for master_item in master_items:
            assert master_item["name"].encode() in response.data
            for master_content in master_item["master_contents"]:
                assert master_content.encode() in response.data
        master_details = master_list["master_details"]
        for master_detail in master_details:
            assert master_detail["name"].encode() in response.data
        for other_master_list_id in other_master_list_ids:
            other_master_list = get_master_list(other_master_list_id["id"], False)
            assert other_master_list["name"].encode() not in response.data
            assert other_master_list["description"].encode() not in response.data
            other_master_items = db.execute("SELECT name FROM master_items WHERE id NOT IN (1, 2)")
            for other_master_item in other_master_items:
                assert other_master_item["name"].encode() not in response.data
                for master_content in master_item["master_contents"]:
                    assert master_content.encode() in response.data
            other_master_details = other_master_list["master_details"]
            for other_master_detail in other_master_details:
                assert other_master_detail["name"].encode() not in response.data
        untethered_contents = db.execute("SELECT item_id, content FROM untethered_content WHERE list_id = 5").fetchall()
        for ut in untethered_contents:
            assert ut["content"].encode() in response.data
            item_name = db.execute("SELECT name FROM items WHERE id = ?", (ut["item_id"],)).fetchone()
            assert item_name["name"].encode() in response.data
        other_untethered_contents = db.execute("SELECT item_id, content FROM untethered_content WHERE list_id != 5").fetchall()
        for out in other_untethered_contents:
            assert out["content"].encode() not in response.data
            item_name = db.execute("SELECT name FROM items WHERE id = ?", (out["item_id"],)).fetchone()
            assert item_name["name"].encode() not in response.data


def test_new_untethered_content(app, client, auth):
    # Get requests
    # You have to be logged in and own the list
    response = client.get("/lists/5/items/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get("/lists/5/items/new")
    assert response.status_code == 403
    auth.login()
    response = client.get("/lists/5/items/new")
    assert response.status_code == 200
    with app.app_context():
        # The master list name and description are shown
        db = get_db()
        db.row_factory = dict_factory
        master_list_id = db.execute("SELECT master_list_id FROM list_tethers WHERE list_id = 5").fetchone()["master_list_id"]
        other_master_list_ids = db.execute("SELECT id FROM master_lists WHERE id != ?", (master_list_id,)).fetchall()
        master_list = get_master_list(master_list_id, False)
        assert master_list["name"].encode() in response.data
        assert master_list["description"].encode() in response.data
        # The master list details are shown
        master_details = master_list["master_details"]
        for master_detail in master_details:
            assert master_detail["name"].encode() in response.data
        # Master details from other master lists are not shown.
        for other_master_list_id in other_master_list_ids:
            other_master_list = get_master_list(other_master_list_id["id"], False)
            other_master_details = other_master_list["master_details"]
            for other_master_detail in other_master_details:
                assert other_master_detail["name"].encode() not in response.data
    # Post requests
    # You have to be logged in and own the list
    auth.logout()
    response = client.get("/lists/5/items/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get("/lists/5/items/new")
    assert response.status_code == 403
    auth.login()
    response = client.get("/lists/5/items/new")
    assert response.status_code == 200
    # Item name is required - covered by test_lists.py
    # The item and untethered content are saved is saved
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute("SELECT id FROM items").fetchall()
        untethered_content_before = db.execute("SELECT id FROM untethered_content").fetchall()
        data = {
            "name": "item name 10",
            "1": "untethered content 6",
            "2": "untethered content 7"
        }
        response = client.post("/lists/5/items/new", data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/5/view"
        items_after = db.execute("SELECT id FROM items").fetchall()
        untethered_content_after = db.execute("SELECT id FROM untethered_content").fetchall()
        assert len(items_after) == len(items_before) + 1
        assert len(untethered_content_after) == len(untethered_content_before) + 2


def test_edit_untethered_content(client, app, auth):
    # Get requests
    # You have to be logged in and own the list.
    response = client.get("/lists/5/items/7/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.get("/lists/5/items/7/edit")
    assert response.status_code == 403
    auth.login()
    response = client.get("/lists/5/items/7/edit")
    assert response.status_code == 200
    # The item must be related to the list
    response = client.get("/lists/5/items/1/edit")
    assert response.status_code == 400
    with app.app_context():
        # The master list name and description are shown
        response = client.get("/lists/5/items/7/edit")
        db = get_db()
        db.row_factory = dict_factory
        master_list_id = db.execute("SELECT master_list_id FROM list_tethers WHERE list_id = 5").fetchone()["master_list_id"]
        other_master_list_ids = db.execute("SELECT id FROM master_lists WHERE id != ?", (master_list_id,)).fetchall()
        master_list = get_master_list(master_list_id, False)
        assert master_list["name"].encode() in response.data
        assert master_list["description"].encode() in response.data
        # The master list details are shown
        master_details = master_list["master_details"]
        for master_detail in master_details:
            assert master_detail["name"].encode() in response.data
        # Master details from other master lists are not shown.
        for other_master_list_id in other_master_list_ids:
            other_master_list = get_master_list(other_master_list_id["id"], False)
            other_master_details = other_master_list["master_details"]
            for other_master_detail in other_master_details:
                assert other_master_detail["name"].encode() not in response.data
    # Post requests
    # User must be logged in and own the list
    auth.logout()
    data = {
        "name": "item name 7 updated",
        "1": "untethered content 1 updated",
        "2": "untethered content 2 updated"
    }
    response = client.post("/lists/5/items/7/edit", data=data)
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.post("/lists/5/items/7/edit", data=data)
    assert response.status_code == 403
    # Item name is required
    auth.login()
    data["name"] = ""
    response = client.post("/lists/5/items/7/edit", data=data)
    assert b"Name is required" in response.data
    # The item is saved
    data["name"] = "item name 7 updated"
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute("SELECT name FROM items").fetchall()
        untethered_content_before = db.execute("SELECT content FROM untethered_content WHERE list_id = 5").fetchall()
        other_untethered_content_before = db.execute("SELECT content FROM untethered_content WHERE list_id != 5").fetchall()
        response = client.post("/lists/5/items/7/edit", data=data)
        items_after = db.execute("SELECT name FROM items").fetchall()
        untethered_content_after = db.execute("SELECT content FROM untethered_content").fetchall()
        other_untethered_content_after = db.execute("SELECT content FROM untethered_content WHERE list_id != 5").fetchall()
        assert items_after[6] != items_before[6]
        assert items_after[:6] + items_after[7:] == items_before[:6] + items_before[7:]
        assert untethered_content_before != untethered_content_after
        assert other_untethered_content_before == other_untethered_content_after
        # Redirect to the lists's view layout
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/5/view"


def test_delete_untethered_content(app, client, auth):
    # User must be logged in and own the list
    response = client.post("/lists/5/items/7/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login("other", "other")
    response = client.post("/lists/5/items/7/delete")
    assert response.status_code == 403
    auth.login()
    with app.app_context():
        db = get_db()
        db.row_factory = dict_factory
        items_before = db.execute('SELECT id, name FROM items').fetchall()
        untethered_content_before = db.execute("SELECT id, content FROM untethered_content").fetchall()
        relations_before = db.execute("SELECT list_id, item_id FROM list_item_relations").fetchall()
        response = client.post('/lists/5/items/7/delete')
        items_after = db.execute("SELECT id, name FROM items").fetchall()
        untethered_content_after = db.execute("SELECT id, content FROM untethered_content").fetchall()
        relations_after = db.execute("SELECT list_id, item_id FROM list_item_relations").fetchall()
        # Only this item gets deleted
        assert db.execute("SELECT id FROM items WHERE id = 7").fetchone() == None
        assert db.execute("SELECT COUNT(id) AS count FROM items").fetchone()["count"] == len(items_before) - 1
        # Only this untethered content gets deleted
        assert db.execute("SELECT id FROM untethered_content WHERE item_id = 7").fetchone() == None
        assert db.execute("SELECT COUNT(id) AS count FROM untethered_content").fetchone()["count"] == len(untethered_content_before) - 2
        # Only this list item relation gets deleted
        assert db.execute("SELECT id FROM list_item_relations WHERE item_id = 7").fetchone() == None
        assert db.execute("SELECT COUNT(id) AS count FROM list_item_relations").fetchone()["count"] == len(relations_before) - 1
        assert response.status_code == 302
        assert response.headers["Location"] == "/lists/5/view"
        

def test_new_detail(client, app, auth):
    # You can't add details to a tethered list
    auth.login()
    response = client.get("/lists/5/details/new")
    assert response.status_code == 403
    data = dict(name="name", description="description")
    response = client.post("/lists/5/details/new", data=data)
    assert response.status_code == 403


def test_edit_list(app, client, auth):
    # You can't edit a tethered list
    auth.login()
    response = client.get("/lists/5/edit")
    assert response.status_code == 403
    data = dict(name="update", description="update")
    response = client.post("/lists/5/edit", data=data)
    assert response.status_code == 403
