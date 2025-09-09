import pytest
from incontext.db import get_db


def test_index_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("master-agents/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-agents/")
    assert response.status_code == 403
    # user must be admin
    auth.login("test", "test")
    response = client.get("master-agents/")
    assert response.status_code == 200
    # master agent data gets served
    assert b"master agent name 1" in response.data
    assert b"master agent description 1" in response.data
    assert b"master agent name 2" in response.data
    assert b"master agent description 2" in response.data
    assert b"master agent name 3" in response.data
    assert b"master agent description 3" in response.data


def test_new_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("/master-agents/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("/master-agents/new")
    assert response.status_code == 403
    auth.login()
    response = client.get("/master-agents/new")
    assert response.status_code == 200
    # agent models get served
    with app.app_context():
        db = get_db()
        agent_models = db.execute("SELECT model_name FROM agent_models")
        for agent_model in agent_models:
            assert agent_model["model_name"].encode() in response.data
    # data validation
    response = client.post(
        "master-agents/new",
        data={
			"name": "",
			"description": "master agent description 4",
			"model_id": "1",
			"role": "master agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/new",
        data={
			"name": "master agent name 4",
			"description": "master agent description 4",
			"model_id": "",
			"role": "master agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/new",
        data={
			"name": "master agent name 4",
			"description": "master agent description 4",
			"model_id": "1",
			"role": "",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/new",
        data={
			"name": "master agent name 4",
			"description": "master agent description 4",
			"model_id": "1",
			"role": "master agent role 4",
            "instructions": ""
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    # master agent is saved to database
    response = client.post(
        "master-agents/new",
        data = {
            "name": "master agent name 4",
            "description": "master agent description 4",
            "model_id": "1",
            "role": "master agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    with app.app_context():
        db = get_db()
        master_agents = db.execute("SELECT * FROM master_agents WHERE creator_id = 2").fetchall()
        assert len(master_agents) == 4
        new_master_agent = master_agents[-1]
        assert new_master_agent["name"] == "master agent name 4"
        assert new_master_agent["description"] == "master agent description 4"
        assert new_master_agent["model_id"] == 1
        assert new_master_agent["role"] == "master agent role 4"
        assert new_master_agent["instructions"] == "Reply with one word: Working"
    # redirected to master_agents.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-agents/"


def test_view_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("master-agents/1/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user doesn't have to be admin or creator
    auth.login("other", "other")
    response = client.get("master-agents/1/view")
    assert response.status_code == 200
    # master agent data gets served
    assert b"master agent name 1" in response.data
    assert b"master agent description 1" in response.data
    assert b"GPT-4.1 nano" in response.data
    assert b"OpenAI" in response.data
    assert b"master agent role 1" in response.data
    assert b"Reply with one word: Working" in response.data
    # do not need to test that other data does not get served
    # because the template only accepts one of each parameter.


def test_edit_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("/master-agents/1/edit")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-agents/1/edit")
    assert response.status_code == 403
    # auth.login("admin2", "admin2")
    auth.login("admin2", "admin2")
    response = client.get("master-agents/1/edit")
    assert response.status_code == 200
    # master agent data gets served
    assert b"master agent name 1" in response.data
    assert b"master agent description 1" in response.data
    assert b"GPT-4.1 nano" in response.data
    assert b"master agent role 1" in response.data
    assert b"Reply with one word: Working" in response.data
    # data validation
    response = client.post(
        "master-agents/1/edit",
        data={
			"name": "",
			"description": "master agent description 1 updated",
			"model_id": "3",
			"role": "master agent role 1 updated",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/1/edit",
        data={
			"name": "master agent name 1 updated",
			"description": "master agent description 1 updated",
			"model_id": "",
			"role": "master agent role 1 updated",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/1/edit",
        data={
			"name": "master agent name 1 updated",
			"description": "master agent description 1 updated",
			"model_id": "1",
			"role": "",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/1/edit",
        data={
			"name": "master agent name 1 updated",
			"description": "master agent description 1 updated",
			"model_id": "1",
			"role": "master agent role 1 updated",
            "instructions": ""
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    # changes are saved to database without affecting other data
    with app.app_context():
        db = get_db()
        master_agents_before = db.execute("SELECT * FROM master_agents").fetchall()
        response = client.post(
            "master-agents/1/edit",
            data={
                "name": "master agent name 1 updated",
                "description": "master agent description 1 updated",
                "model_id": "2",
                "role": "master agent role 1 updated",
                "instructions": "Reply with one word: Working updated"
            }
        )
        master_agents_after = db.execute("SELECT * FROM master_agents").fetchall()
        assert master_agents_after[1:] == master_agents_before[1:]
        assert master_agents_after[0] != master_agents_before[0]
        assert master_agents_after[0]["name"] == "master agent name 1 updated"
        assert master_agents_after[0]["description"] == "master agent description 1 updated"
        assert master_agents_after[0]["model_id"] == 2
        assert master_agents_after[0]["role"] == "master agent role 1 updated"
        assert master_agents_after[0]["instructions"] == "Reply with one word: Working updated"
    # redirected to masters.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/master-agents/'


def test_delete_master_agent(client, auth, app):
    # user must be logged in
    response = client.post("/master-agents/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.post("master-agents/1/delete")
    assert response.status_code == 403
    auth.login("admin2", "admin2")
    with app.app_context():
        # master agent gets deleted
        db = get_db()
        master_agents_before = db.execute("SELECT * FROM master_agents").fetchall()
        response = client.post("master-agents/1/delete")
        master_agents_after = db.execute("SELECT * FROM master_agents").fetchall()
        assert master_agents_after ==  master_agents_before[1:]
        assert len(master_agents_after) == len(master_agents_before) - 1
    # redirected to lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-agents/"
