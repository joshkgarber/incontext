import pytest
from incontext.db import get_db, dict_factory
from incontext.lists import get_user_lists
from incontext.contexts import get_unrelated_lists
from tests.test_db import get_other_tables


def test_index(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("/contexts/")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data unchanged
        # Make the request
        auth.login()
        response = client.get("/contexts/")
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before # Data unchanged
        # Serve context name and description for those owned by the user
        contexts = get_db().execute("SELECT * FROM contexts").fetchall()
        for context in contexts:
            if context["creator_id"] == 2:
                assert context["name"].encode() in response.data
                assert context["description"].encode() in response.data
            else:
                assert context["name"].encode() not in response.data
                assert context["description"].encode() not in response.data


def test_new_get(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("/contexts/new")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data unchanged
        # Make the request
        auth.login()
        response = client.get("/contexts/new")
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before # Data unchanged


def test_new_post(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        data = dict(name="", description="")
        path = "/contexts/new"
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data unchanged
        # Data validation
        auth.login()
        # Name
        data["description"] = "new context description"
        response = client.post(path, data=data)
        assert b"Name and description are required." in response.data
        assert get_other_tables() == all_tables_before # Data unchanged
        # Description
        data["name"] = "new context name"
        data["description"] = ""
        response = client.post(path, data=data)
        assert b"Name and description are required." in response.data
        assert get_other_tables() == all_tables_before # Data unchanged
        # Get affected tables before the request
        db = get_db()
        db.row_factory = dict_factory
        contexts_before = db.execute("SELECT * FROM contexts")
        # Get other tables before the request
        other_tables_before = get_other_tables(["contexts"])
        # Make the request
        data["description"] = "new context description"
        response = client.post(path, data=data)
        # Redirected to contexts index
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/"
        # Other tables remain unchangd
        assert get_other_tables(["contexts"]) == other_tables_before
        # The new context is saved and the other rows are unchanged
        contexts_after = db.execute("SELECT * FROM contexts").fetchall()
        new_context = [context for context in contexts_after if context["name"] == "new context name"]
        assert len(new_context) == 1
        new_context = new_context[0]
        assert new_context["description"] == "new context description"
        for context in contexts_after:
            if context != new_context:
                assert context in contexts_before


def test_view(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        path = "/contexts/1/view"
        # User must be logged in
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data unchanged
        # User must have access to the context
        auth.login("other", "other")
        response = client.get(path)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data unchanged
        # Context must exist
        auth.login()
        response = client.get("/contexts/bogus/view")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data unchanged
        # Make the request
        response = client.get(path)
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before # Data unchanged
        # Serve name and description of connected lists and not other lists
        db = get_db()
        lists = db.execute(
            "SELECT l.name, l.description, r.context_id FROM lists l"
            " JOIN context_list_relations r ON r.list_id = l.id"
        ).fetchall()
        for listo in lists:
            if listo["context_id"] == 1:
                assert listo["name"].encode() in response.data
                assert listo["description"].encode() in response.data
            else:
                assert listo["name"].encode() not in response.data
                assert listo["description"].encode() not in response.data
        # Serve name of related conversations and their agents
        conversations = db.execute(
            "SELECT c.id, c.name, c.created, a.id AS agent_id, a.name AS agent_name, ccr.context_id, ctx.name AS context_name, ctx.creator_id"
            " FROM conversations c"
            " JOIN conversation_agent_relations r ON c.id = r.conversation_id"
            " JOIN agents a ON r.agent_id = a.id"
            " JOIN context_conversation_relations ccr ON ccr.conversation_id = c.id"
            " JOIN contexts ctx ON ctx.id = ccr.context_id"
        ).fetchall()
        for conversation in conversations:
            agent_name = conversation["agent_name"]
            context_name = conversation["context_name"]
            if conversation["context_id"] == 1:
                assert conversation["name"].encode() in response.data
                assert conversation["agent_name"].encode() in response.data
            else:
                assert conversation["name"].encode() not in response.data
                if conversation["agent_name"] != agent_name:
                    assert conversation["agent_name"].encode() not in response.data
        # Serve messages for conversations in this context, not others
        messages = db.execute(
            "SELECT m.content, ccr.context_id FROM messages m"
            " JOIN context_conversation_relations ccr"
            " ON ccr.conversation_id = m.conversation_id"
        ).fetchall()
        for message in messages:
            if message["context_id"] == 1:
                assert message["content"].encode() in response.data
            else:
                assert message["content"].encode() not in response.data
       

def test_edit_get(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        path = "/contexts/1/edit"
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data is unchanged
        # User must have access
        auth.login("other", "other")
        response = client.get(path)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data is unchanged
        # Context must exist
        auth.login()
        response = client.get("/contexts/bogus/edit")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data is unchanged
        # Make the request
        response = client.get("/contexts/1/edit")
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before # Data is unchanged
        # The context name and description are served and no other contexts are served
        contexts = get_db().execute("SELECT * FROM contexts").fetchall()
        for context in contexts:
            if context["id"] == 1:
                assert context["name"].encode() in response.data
                assert context["description"].encode() in response.data
            else:
                assert context["name"].encode() not in response.data
                assert context["description"].encode() not in response.data
  

def test_edit_post(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        data = dict(name="", description="")
        path = "/contexts/1/edit"
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Context must exist
        auth.login()
        response = client.post("/contexts/bogus/edit", data=data)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # Data validation
        # Name
        data["description"] == "updated description"
        response = client.post(path, data=data)
        assert b"Name and description are required." in response.data
        assert get_other_tables() == all_tables_before
        # Description
        data["description"] = ""
        data["name"] = "updated name"
        response = client.post(path, data=data)
        assert b"Name and description are required." in response.data
        assert get_other_tables() == all_tables_before
        # Get affected tables before
        db = get_db()
        contexts_before = db.execute("SELECT * FROM contexts").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["contexts"])
        # Make the request
        data["description"] = "updated description"
        response = client.post(path, data=data)
        # Redirected to context view
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/1/view"
        # Get affected tables after
        contexts_after = db.execute("SELECT * FROM contexts").fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["contexts"])
        # Other tables are unchanged
        assert other_tables_after == other_tables_before
        # Expected rows of the affected tables are changed while other rows are unchanged
        edited_contexts = [context for context in contexts_after if context["id"] == 1 and context["name"] == "updated name" and context["description"] == "updated description"]
        assert len(edited_contexts) == 1
        edited_context = edited_contexts[0]
        for context in contexts_after:
            if context != edited_context:
                assert context in contexts_before
        assert len(contexts_before) == len(contexts_after)
 

def test_delete(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.post("/contexts/1/delete")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access
        auth.login("other", "other")
        response = client.post("/contexts/1/delete")
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Context must exist
        response = client.post("contexts/bogus/delete")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # Get affected tables before
        db = get_db()
        contexts_before = db.execute("SELECT * FROM contexts").fetchall()
        context_list_relations_before = db.execute("SELECT * FROM context_list_relations").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["contexts", "context_list_relations"])
        # Make request
        auth.login()
        response = client.post("contexts/1/delete")
        # Redirect to contexts index
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/"
        # Get other tables after
        other_tables_after = get_other_tables(["contexts", "context_list_relations"])
        # Assert other tables didn't change
        assert other_tables_after == other_tables_before
        # Get affected tables after
        contexts_after = db.execute("SELECT * FROM contexts").fetchall()
        context_list_relations_after = db.execute("SELECT * FROM context_list_relations").fetchall()
        # Assert the affected rows are gone and the other rows are unchanged
        assert len(contexts_after) == len(contexts_before) - 1
        affected_context = next((c for c in contexts_before if c["id"] == 1), None)
        assert affected_context is not None
        for context in contexts_after:
            assert context in contexts_before
            assert context != affected_context
        clr_deletion_count = 0
        for clr in context_list_relations_before:
            if clr["context_id"] == 1:
                assert clr not in context_list_relations_after
                clr_deletion_count += 1
            else:
                assert clr in context_list_relations_after
        assert len(context_list_relations_before) == len(context_list_relations_after) + clr_deletion_count


def test_connect_list_get(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        path = "/contexts/1/new-list"
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data unchanged
        # User must have access
        auth.login("other", "other")
        response = client.get(path)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data unchanged
        # Context must exist
        auth.login()
        response = client.get("/contexts/bogus/new-list")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data unchanged
        # Make the request
        response = client.get(path)
        assert response.status_code == 200
        # The user's lists are shown (if not already connected) and other lists are not shown
        db = get_db()
        lists = db.execute(
            "SELECT l.creator_id, l.name, l.description, r.context_id"
            " FROM lists l LEFT JOIN context_list_relations r"
            " ON l.id = r.list_id"
        ).fetchall()
        for listo in lists:
            print(f"list name: {listo["name"]} | context id: {listo["context_id"]}")
            if listo["context_id"]:
                assert listo["name"].encode() not in response.data
                assert listo["description"].encode() not in response.data
            else:
                if listo["creator_id"] == 1:
                    assert listo["name"].encode() in response.data
                    assert listo["description"].encode() in response.data


def test_connect_list_post(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        data = dict(list_id="")
        path = "/contexts/1/new-list"
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Context must exist
        auth.login()
        response = client.post("/contexts/bogus/new-list", data=data)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # User must have access to the list
        data["list_id"] = 3
        response = client.post(path, data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Get affected tables before the request
        db = get_db()
        context_list_relations_before = db.execute("SELECT * FROM context_list_relations").fetchall()
        # Get other tables before the request
        other_tables_before = get_other_tables(["context_list_relations"])
        # Make the request
        data["list_id"] = 5
        response = client.post(path, data=data)
        # Redirected to context view
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/1/view"
        # Get affected tables after the request
        context_list_relations_after = db.execute("SELECT * FROM context_list_relations").fetchall()
        # Get other tables after the request
        other_tables_after = get_other_tables(["context_list_relations"])
        # Assert that other tables have not changed
        assert other_tables_after == other_tables_before
        # Assert that the expected rows have been added to the affected tables and other rows have not changed
        new_relation = next((relation for relation in context_list_relations_after if relation["list_id"] == 5 and relation["context_id"] == 1), None)
        assert new_relation is not None
        for relation in context_list_relations_after:
            if relation != new_relation:
                assert relation in context_list_relations_before
        assert len(context_list_relations_after) == len(context_list_relations_before) + 1


def test_remove_list(client, auth, app):
    with app.app_context():
        path = "/contexts/1/remove-list"
        data = dict(list_id="1")
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access to the context
        auth.login("other", "other")
        response = client.post("/contexts/3/remove-list", data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # User must have access to the list
        auth.login()
        data["list_id"] = 3
        response = client.post(path, data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Context must exist
        response = client.post("/contexts/bogus/remove-list", data=data)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # List must exist
        data["list_id"] = "bogus"
        response = client.post(path, data=data)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # List is required
        data = {}
        response = client.post(path, data=data)
        assert response.status_code == 400
        assert get_other_tables() == all_tables_before
        # Get the affected tables before the request
        db = get_db()
        context_list_relations_before = db.execute("SELECT * FROM context_list_relations").fetchall()
        # Get the other tables before the request
        other_tables_before = get_other_tables(["context_list_relations"])
        # Make the request
        data["list_id"] = "1"
        response = client.post(path, data=data)
        # Redirected to context view
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/1/view"
        # Other tables are unchanged
        assert get_other_tables(["context_list_relations"]) == other_tables_before
        # Affected row is removed while other rows are unchanged.
        context_list_relations_after = db.execute("SELECT * FROM context_list_relations").fetchall()
        for clr in context_list_relations_after:
            if clr["context_id"] == 1:
                assert clr["list_id"] != 1
            assert clr in context_list_relations_before
        assert len(context_list_relations_after) == len(context_list_relations_before) - 1
