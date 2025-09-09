import pytest
from incontext.db import get_db


def test_index_agents(client, auth):
    # user must be logged in
    response = client.get("/agents/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/agents/")
    assert response.status_code == 200
    # user's agent data gets served
    assert b"agent name 1" in response.data
    assert b"agent description 1" in response.data
    assert b"agent name 2" in response.data
    assert b"agent description 2" in response.data
    # other user's agent data not served
    assert b"agent name 3" not in response.data
    assert b"agent description 3" not in response.data


def test_new_agent(app, client, auth):
    # user must be logged in
    response = client.get("/agents/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/agents/new")
    assert response.status_code == 200
    # data validation
    response = client.post(
        "agents/new",
        data={
			"name": "",
			"description": "agent description 4",
			"model_id": "1",
			"role": "agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b"Name, model, role, and instructions are all required." in response.data
    response = client.post(
        "agents/new",
        data={
			"name": "agent name 4",
			"description": "agent description 4",
			"model_id": "",
			"role": "agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b"Name, model, role, and instructions are all required." in response.data
    response = client.post(
        "agents/new",
        data={
			"name": "agent name 4",
			"description": "agent description 4",
			"model_id": "1",
			"role": "",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b"Name, model, role, and instructions are all required." in response.data
    response = client.post(
        "agents/new",
        data={
			"name": "agent name 4",
			"description": "agent description 4",
			"model_id": "1",
			"role": "agent role 4",
            "instructions": ""
        }
    )
    assert b"Name, model, role, and instructions are all required." in response.data
    # agent is saved to database
    response = client.post(
        "/agents/new",
        data = {
            "name": "agent name 4",
            "description": "agent description 4",
            "model_id": "1",
            "role": "agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    with app.app_context():
        db = get_db()
        agents = db.execute("SELECT * FROM agents WHERE creator_id = 2").fetchall()
        assert len(agents) == 3
        new_agent = agents[-1]
        assert new_agent["name"] == "agent name 4"
        assert new_agent["description"] == "agent description 4"
        assert new_agent["model_id"] == 1
        assert new_agent["role"] == "agent role 4"
        assert new_agent["instructions"] == "Reply with one word: Working"
    # redirected to agents.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/agents/"


def test_view_agent(app, client, auth):
    # user must be logged in
    response = client.get("agents/1/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be agent creator
    auth.login("other", "other")
    response = client.get("agents/1/view")
    assert response.status_code == 403
    auth.login()
    response = client.get("agents/1/view")
    assert response.status_code == 200
    # agent data gets served
    assert b"agent name 1" in response.data
    assert b"agent description 1" in response.data
    assert b"GPT-4.1 nano" in response.data
    assert b"OpenAI" in response.data
    assert b"agent role 1" in response.data
    assert b"Reply with one word: Working" in response.data
    # do not need to test that other data does not get served
    # because the template only accepts one of each parameter.


def test_edit_agent(app, client, auth):
    # user must be logged in
    response = client.get("/agents/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be agent creator
    auth.login("other", "other")
    response = client.get("agents/1/edit")
    assert response.status_code == 403
    auth.login()
    response = client.get("agents/1/edit")
    assert response.status_code == 200
    # agent data gets served
    assert b"agent name 1" in response.data
    assert b"agent description 1" in response.data
    assert b"GPT-4.1 nano" in response.data
    assert b"agent role 1" in response.data
    assert b"Reply with one word: Working" in response.data
    # data validation
    response = client.post(
        "agents/1/edit",
        data={
			"name": "",
			"description": "agent description 1 updated",
			"model_id": "3",
			"role": "agent role 1 updated",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "agents/1/edit",
        data={
			"name": "agent name 1 updated",
			"description": "agent description 1 updated",
			"model_id": "",
			"role": "agent role 1 updated",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "agents/1/edit",
        data={
			"name": "agent name 1 updated",
			"description": "agent description 1 updated",
			"model_id": "1",
			"role": "",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "agents/1/edit",
        data={
			"name": "agent name 1 updated",
			"description": "agent description 1 updated",
			"model_id": "1",
			"role": "agent role 1 updated",
            "instructions": ""
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    # changes are saved to database without affecting other data
    with app.app_context():
        db = get_db()
        agents_before = db.execute("SELECT * FROM agents").fetchall()
        response = client.post(
            "agents/1/edit",
            data={
                "name": "agent name 1 updated",
                "description": "agent description 1 updated",
                "model_id": "2",
                "role": "agent role 1 updated",
                "instructions": "Reply with one word: Working updated"
            }
        )
        agents_after = db.execute("SELECT * FROM agents").fetchall()
        assert agents_after[1:] == agents_before[1:]
        assert agents_after[0] != agents_before[0]
        assert agents_after[0]["name"] == "agent name 1 updated"
        assert agents_after[0]["description"] == "agent description 1 updated"
        assert agents_after[0]["model_id"] == 2
        assert agents_after[0]["role"] == "agent role 1 updated"
        assert agents_after[0]["instructions"] == "Reply with one word: Working updated"
    # redirected to masters.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/agents/'


def test_delete_agent(client, auth, app):
    # user must be logged in
    response = client.post("/agents/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be agent creator
    auth.login("other", "other")
    response = client.post("agents/1/delete")
    assert response.status_code == 403
    auth.login()
    with app.app_context():
        # agent gets deleted
        db = get_db()
        agents_before = db.execute("SELECT * FROM agents").fetchall()
        response = client.post("agents/1/delete")
        agents_after = db.execute("SELECT * FROM agents").fetchall()
        assert agents_after ==  agents_before[1:]
        assert len(agents_after) == len(agents_before) - 1
    # redirected to lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/agents/"


def test_new_tethered_agent(client, auth, app):
    # user must be logged in
    response = client.get("/agents/new-tethered")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/agents/new-tethered")
    assert response.status_code == 200
    # master agent information served
    assert b"master agent name 1" in response.data
    assert b"master agent description 1" in response.data
    assert b"master agent name 2" in response.data
    assert b"master agent description 2" in response.data
    assert b"master agent name 3" in response.data
    assert b"master agent description 3" in response.data
    # tethered agent is saved to database
    response = client.post(
        "/agents/new-tethered",
        data = {
            "master_agent_id": "1",
        }
    )
    with app.app_context():
        db = get_db()
        tethered_agents = db.execute("SELECT * FROM tethered_agents WHERE creator_id = 2").fetchall()
        assert len(tethered_agents) == 3
        new_tethered_agent = tethered_agents[-1]
        assert new_tethered_agent["master_agent_id"] == 1
    # redirected to agents.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/agents/"


def test_delete_tethered_agent(client, auth, app):
    # user must be logged in
    response = client.post("agents/1/delete-tethered")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be tethered agent creator
    auth.login("other", "other")
    response = client.post("agents/1/delete-tethered")
    assert response.status_code == 403
    auth.login()
    with app.app_context():
        # tethered agent gets deleted
        db = get_db()
        tethered_agents_before = db.execute("SELECT * FROM tethered_agents").fetchall()
        response = client.post("agents/1/delete-tethered")
        tethered_agents_after = db.execute("SELECT * FROM tethered_agents").fetchall()
        assert tethered_agents_after ==  tethered_agents_before[1:]
        assert len(tethered_agents_after) == len(tethered_agents_before) - 1
    # redirected to lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/agents/"


