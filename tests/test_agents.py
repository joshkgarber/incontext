import pytest
from incontext.db import get_db, dict_factory
from tests.test_db import get_other_tables
from flask import get_flashed_messages


def test_index(app, client, auth):
    with app.app_context():
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("/agents/")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data doesn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # Make the request
        auth.login()
        response = client.get("/agents/")
        assert response.status_code == 200
        # Data doesn't change
        all_tables_after = get_other_tables()
        assert all_tables_after == all_tables_before
        # The user's agent data gets served and other user's agent data is not
        db = get_db()
        agents = db.execute("SELECT * FROM agents")
        for agent in agents:
            if agent["creator_id"] == 2:
                assert agent["name"].encode() in response.data
                assert agent["description"].encode() in response.data
            else:
                assert agent["name"].encode() not in response.data
                assert agent["description"].encode() not in response.data


def test_new_get(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("/agents/new")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # Data doesn't change
        assert get_other_tables() == all_tables_before
        # Make the request
        auth.login()
        response = client.get("/agents/new")
        assert response.status_code == 200
        # Data doesn't change
        assert get_other_tables() == all_tables_before
        # All model names are served
        models = get_db().execute("SELECT * FROM agent_models")
        for model in models:
            assert model["model_name"].encode() in response.data


def test_new_post(app, client, auth):
    with app.app_context():
        all_tables_before = get_other_tables()
        # User must be logged in
        data = dict(name="", description="", model_id="", role="", instructions="")
        path = "/agents/new"
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Data validation
        auth.login()
        response = client.post(path, data=data)
        assert b"Name, model, role, and instructions are all required." in response.data
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Name
        data["description"] == "new agent description"
        data["model_id"] == "1"
        data["role"] == "new agent role"
        data["instructions"] == "new agent instructions"
        response = client.post(path, data=data)
        assert b"Name, model, role, and instructions are all required." in response.data
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Description
        data["name"] = "new agent name"
        data["description"] = ""
        response = client.post(path, data=data)
        assert b"Name, model, role, and instructions are all required." in response.data
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Model id
        data["model_id"] = ""
        data["description"] = "new model description"
        response = client.post(path, data=data)
        assert b"Name, model, role, and instructions are all required." in response.data
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Role
        data["model_id"] = "1"
        data["role"] = ""
        response = client.post(path, data=data)
        assert b"Name, model, role, and instructions are all required." in response.data
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Instructions
        data["role"] = "new agent role"
        data["instructions"] = ""
        response = client.post(path, data=data)
        assert b"Name, model, role, and instructions are all required." in response.data
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Get the affected tables before
        db = get_db()
        db.row_factory = dict_factory
        agents_before = db.execute("SELECT * FROM agents").fetchall()
        # Get the other tables before
        other_tables_before = get_other_tables(["agents"])
        # Make the request
        data["instructions"] = "new agent instructions"
        response = client.post(path, data=data)
        # Get the affected tables after
        agents_after = db.execute("SELECT * FROM agents").fetchall()
        # Get the other tables after
        other_tables_after = get_other_tables(["agents"])
        # Assert the new rows are in the affected tables after
        new_agent = [agent for agent in agents_after if agent["name"] == "new agent name"]
        assert len(new_agent) == 1
        new_agent_id = new_agent[0]["id"]
        # Assert that all other rows in the affected tables after comprise the affected tables before
        other_rows = [agent for agent in agents_after if agent["id"] != new_agent_id]
        assert other_rows == agents_before
        # Assert that the other tables after is equal to the other tables before
        assert other_tables_after == other_tables_before
        # Redirect to agents.index
        assert response.status_code == 302
        assert response.headers["Location"] == "/agents/"


def test_view(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("agents/1/view")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data doesn't change
        # User must have permission
        auth.login("other", "other")
        response = client.get("agents/1/view")
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Agent must exist
        auth.login()
        response = client.get("agents/bogus/view")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Make request
        response = client.get("agents/1/view")
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Agent data gets served while other agent data does not
        db = get_db()
        agents = db.execute("SELECT * FROM agents").fetchall()
        model_id = next((agent["model_id"] for agent in agents if agent["id"] == 1), None) # Model id and name might be the same (see below)
        assert model_id is not None
        model_name = db.execute(f"SELECT model_name FROM agent_models WHERE id = {model_id}").fetchone()["model_name"]
        for agent in agents:
            if agent["id"] == 1:
                assert agent["name"].encode() in response.data
                assert agent["description"].encode() in response.data
                assert model_name.encode() in response.data
                assert agent["role"].encode() in response.data
                assert agent["instructions"].encode() in response.data
            else:
                assert agent["name"].encode() not in response.data
                assert agent["description"].encode() not in response.data
                other_model_name = db.execute(f"SELECT model_name FROM agent_models WHERE id = {agent['model_id']}").fetchone()["model_name"]
                if other_model_name != model_name:
                    assert other_model_name.encode() not in response.data
                assert agent["role"].encode() not in response.data
                assert agent["instructions"].encode() not in response.data
        contexts = db.execute(
            "SELECT c.name, c.description, r.agent_id FROM contexts c"
            " JOIN context_agent_relations r ON r.context_id = c.id"
        ).fetchall()
        context_names = []
        context_descriptions = []
        for context in contexts:
            if context["agent_id"] == 1:
                context_names.append(context["name"])
                assert context["name"].encode() in response.data
                context_descriptions.append(context["description"])
                assert context["description"].encode() in response.data
            else:
                if context["name"] not in context_names:
                    assert context["name"] not in response.data
                if context["description"] not in context_descriptions:
                    assert context["description"] not in response.data


def test_edit_get(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get("/agents/1/edit")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data doesn't change
        # User must have access
        auth.login("other", "other")
        response = client.get("agents/1/edit")
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Agent must exist
        auth.login()
        response = client.get("agents/bogus/edit")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Make the request
        response = client.get("agents/1/edit")
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Agent data gets served and no other agent data is served
        db = get_db()
        agents = db.execute("SELECT * FROM agents").fetchall()
        model_id = next((agent["model_id"] for agent in agents if agent["id"] == 1), None) # Model id might be the same (see below)
        assert model_id is not None
        for agent in agents:
            if agent["id"] == 1:
                assert agent["name"].encode() in response.data
                assert agent["description"].encode() in response.data
                assert f'if (opt.value == "{agent['model_id']}") opt.selected = true;'.encode() in response.data
                assert agent["role"].encode() in response.data
                assert agent["description"].encode() in response.data
            else:
                assert agent["name"].encode() not in response.data
                assert agent["description"].encode() not in response.data
                if agent["model_id"] != model_id:
                    assert f'if (opt.value == "{agent['model_id']}") opt.selected = true;'.encode() not in response.data
                assert agent["role"].encode() not in response.data
                assert agent["instructions"].encode() not in response.data


def test_edit_post(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        data = dict(name="", description="", model_id="", role="", instructions="")
        path = "/agents/1/edit"
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data unchanged
        # User must have access
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data unchanged
        # Agent must exist
        auth.login()
        response = client.post("/agents/bogus/edit", data=data)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data unchanged
        # Data validation
        # Name
        data["description"] = "agent description 1 updated"
        data["model_id"] = "2"
        data["role"] = "agent role 1 updated"
        data["instructions"] = "agent instructions 1 updated"
        response = client.post(path, data=data)
        assert b'Name, model, role, and instructions are all required.' in response.data
        assert get_other_tables() == all_tables_before # Data unchanged
        # Model ID
        data["name"] = "agent name 1 updated"
        data["model_id"] = ""
        response = client.post(path, data=data)
        assert b'Name, model, role, and instructions are all required.' in response.data
        assert get_other_tables() == all_tables_before # Data unchanged
        # Role
        data["model_id"] = "2"
        data["role"] = ""
        response = client.post(path, data=data)
        assert b'Name, model, role, and instructions are all required.' in response.data
        assert get_other_tables() == all_tables_before # Data unchanged
        # Instructions
        data["role"] = "agent role 1 updated"
        data["instructions"] = ""
        response = client.post(path, data=data)
        assert b'Name, model, role, and instructions are all required.' in response.data
        assert get_other_tables() == all_tables_before # Data unchanged
        data["instructions"] = "agent instructions 1 updated"
        # Get affected tables before
        db = get_db()
        db.row_factory = dict_factory
        agents_before = db.execute("SELECT * FROM agents").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["agents"])
        # Make the request
        response = client.post(path, data=data)
        # Redirected to agent view
        assert response.status_code == 302
        assert response.headers["Location"] == "/agents/1/view"
        # Get affected tables after
        agents_after = db.execute("SELECT * FROM agents").fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["agents"])
        # Assert that other tables after = other tables before
        assert other_tables_after == other_tables_before
        # Assert that affected rows are updated as expected while unaffected rows are the same as in affected table before
        for agent in agents_after:
            if agent["id"] == 1:
                assert agent not in agents_before
                assert agent["name"] == data["name"]
                assert agent["description"] == data["description"]
                assert str(agent["model_id"]) == data["model_id"]
                assert agent["role"] == data["role"]
                assert agent["instructions"] == data["instructions"]
            else:
                assert agent in agents_before
        assert len(agents_before) == len(agents_after)


def test_delete(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.post("/agents/1/delete")
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before # Data doesn't change
        # User must have access
        auth.login("other", "other")
        response = client.post("agents/1/delete")
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Agent must exist
        auth.login()
        response = client.post("agents/bogus/delete")
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before # Data doesn't change
        # Get affected tables before the request
        db = get_db()
        db.row_factory = dict_factory
        agents_before = db.execute("SELECT * FROM agents").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["agents"])
        # Make the request
        response = client.post("agents/1/delete")
        # redirected to Agents index
        assert response.status_code == 302
        assert response.headers["Location"] == "/agents/"
        # Get the affected tables after request
        agents_after = db.execute("SELECT * FROM agents").fetchall()
        # Get the other tables after the request
        other_tables_after = get_other_tables(["agents"])
        # Assert other tables have not changed
        assert other_tables_after == other_tables_before
        # Assert that affected rows aren't in affected table after and the remaining rows are unchanged
        deletion_count = 0
        for agent in agents_before:
            if agent["id"] == 1:
                assert agent not in agents_after
                deletion_count += 1
            else:
                assert agent in agents_after
        assert len(agents_after) == len(agents_before) - deletion_count
