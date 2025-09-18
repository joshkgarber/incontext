import pytest
from incontext.db import get_db
from tests.test_db import get_other_tables


def test_index(app, client, auth):
    with app.app_context():
        path = "/conversations/"
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # Make the request
        auth.login()
        response = client.get(path)
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before
        # User's conversation data is shown, other users not
        db = get_db()
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
            if conversation["creator_id"] == 2:
                assert conversation["name"].encode() in response.data
                assert conversation["agent_name"].encode() in response.data
                assert conversation["context_name"].encode() in response.data
            else:
                assert conversation["name"].encode() not in response.data
                if conversation["agent_name"] != agent_name:
                    assert conversation["agent_name"].encode() not in response.data
                if conversation["context_name"] != context_name:
                    assert conversation["context_name"].encode() not in response.data


def test_new_get(client, auth, app):
    with app.app_context():
        path = "/conversations/new?context_id=1"
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access
        auth.login("other", "other")
        response = client.get(path)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Context must exist
        auth.login()
        path = "/conversations/new?context_id=bogus"
        response = client.get(path)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # Make the request
        path = "/conversations/new?context_id=1"
        response = client.get(path)
        assert response.status_code == 200
        assert get_other_tables() == all_tables_before
        # User's agent names are served, others not
        db = get_db()
        agents = db.execute("SELECT * FROM agents").fetchall()
        for agent in agents:
            if agent["creator_id"] == 2:
                assert agent["name"].encode() in response.data
            else:
                assert agent["name"].encode() not in response.data
        # Related context name is served, others not
        contexts = db.execute("SELECT * FROM contexts").fetchall()
        for context in contexts:
            if context["id"] == 1:
                assert context["name"].encode() in response.data
            else:
                assert context["name"].encode() not in response.data


def test_new_post(client, auth, app):
    with app.app_context():
        path = "/conversations/new?context_id=1"
        data = dict(name="", agent_id="")
        # Get all tables before
        all_tables_before = get_other_tables()
        # User must be logged in
        response = client.get(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        assert get_other_tables() == all_tables_before
        # User must have access
        auth.login("other", "other")
        response = client.get(path, data=data)
        assert response.status_code == 403
        assert get_other_tables() == all_tables_before
        # Context must exist
        auth.login()
        path = "/conversations/new?context_id=bogus"
        response = client.post(path, data=data)
        assert response.status_code == 404
        assert get_other_tables() == all_tables_before
        # Data validation
        path = "/conversations/new?context_id=1"
        # Name
        data["agent_id"] = "1"
        response = client.post(path, data=data)
        assert b"Name and agent are required" in response.data
        assert get_other_tables() == all_tables_before
        # Agent ID
        data["agent_id"] = ""
        data["name"] = "new conversation"
        response = client.post(path, data=data)
        assert b"Name and agent are required" in response.data
        assert get_other_tables() == all_tables_before
        # Get affected tables before
        db = get_db()
        conversations_before = db.execute("SELECT * FROM conversations").fetchall()
        conversation_agent_relations_before = db.execute("SELECT * FROM conversation_agent_relations").fetchall()
        context_conversation_relations_before = db.execute("SELECT * FROM context_conversation_relations").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["conversations", "conversation_agent_relations", "context_conversation_relations"])
        # Make the request
        data["agent_id"] = "1"
        response = client.post(path, data=data)
        # Redirected to the context view
        assert response.status_code == 302
        assert response.headers["Location"] == "/contexts/1/view"
        # Get affected tables after
        conversations_after = db.execute("SELECT * FROM conversations").fetchall()
        conversation_agent_relations_after = db.execute("SELECT * FROM conversation_agent_relations").fetchall()
        context_conversation_relations_after = db.execute("SELECT * FROM context_conversation_relations").fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["conversations", "conversation_agent_relations", "context_conversation_relations"])
        # Assert other tables haven't changed
        assert other_tables_after  == other_tables_before
        # Assert expected rows have been created in the affected tables and other rows haven't changed
        new_conversation = [ca for ca in conversations_after if ca["name"] == "new conversation"]
        assert len(new_conversation) == 1
        new_conv = new_conversation[0]
        for ca in conversations_after:
            if ca != new_conv:
                assert ca in conversations_before
        assert len(conversations_after) == len(conversations_before) + 1
        conv_id = new_conv["id"]
        for car in conversation_agent_relations_after:
            if car["conversation_id"] == conv_id:
                assert car["agent_id"] == 1
                assert car not in conversation_agent_relations_before
            else:
                assert car in conversation_agent_relations_before
        assert len(conversation_agent_relations_after) == len(conversation_agent_relations_before) + 1
        for ccr in context_conversation_relations_after:
            if ccr["conversation_id"] == conv_id:
                assert ccr["context_id"] == 1
                assert ccr not in context_conversation_relations_before
            else:
                assert ccr in context_conversation_relations_before
        assert len(context_conversation_relations_after) == len(context_conversation_relations_before) + 1


def test_edit_get(app, client, auth):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        path = "/conversations/1/edit"
        # User must be logged in
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # User must have access
        auth.login("other", "other")
        response = client.get(path)
        assert response.status_code == 403
        # Conversation must exist
        auth.login()
        response = client.get("/conversations/bogus/edit")
        assert response.status_code == 404
        # Make the request
        response = client.get(path)
        assert response.status_code == 200
        # Conversation name is served, others not
        db = get_db()
        conversations = db.execute(
            "SELECT c.name, c.id"
            " FROM conversations c"
        ).fetchall()
        for c in conversations:
            if c["id"] == 1:
                assert c["name"].encode() in response.data
            else:
                assert c["name"].encode() not in response.data
        # User's agents names are served, others not
        agents = db.execute("SELECT * FROM agents").fetchall()
        for agent in agents:
            if agent["creator_id"] == 2:
                assert agent["name"].encode() in response.data
            else:
                assert agent["name"].encode() not in response.data
        # Data hasn't changed
        assert get_other_tables() == all_tables_before


def test_edit_post(app, client, auth):
    with app.app_context():
        all_tables_before = get_other_tables()
        path = "/conversations/1/edit"
        data = dict(name="", agent_id="")
        # User must be logged in
        response = client.post(path, data=data)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # User must have access
        auth.login("other", "other")
        response = client.post(path, data=data)
        assert response.status_code == 403
        # Conversation must exist
        auth.login()
        path = "/conversations/bogus/edit"
        response = client.post(path, data=data)
        assert response.status_code == 404
        path = "/conversations/1/edit"
        # Data validation
        # Name
        data["agent_id"] = "2"
        response = client.post(path, data=data)
        assert b"Name and agent are required" in response.data
        # Agent ID
        data["agent_id"] = ""
        data["name"] = "conversation name updated"
        response = client.post(path, data=data)
        assert b"Name and agent are required" in response.data
        # After all that, data hasn't changed.
        assert get_other_tables() == all_tables_before
        # Get affected tables before
        db = get_db()
        conversations_before = db.execute("SELECT * FROM conversations").fetchall()
        conversation_agent_relations_before = db.execute("SELECT * FROM conversation_agent_relations").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["conversations", "conversation_agent_relations"])
        # Make the request
        data["agent_id"] = "2"
        response = client.post(path, data=data)
        # Redirected to the conversations index 
        assert response.status_code == 302
        assert response.headers["Location"] == "/conversations/"
        # Get affected tables after
        conversations_after = db.execute("SELECT * FROM conversations").fetchall()
        conversation_agent_relations_after = db.execute("SELECT * FROM conversation_agent_relations").fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["conversations", "conversation_agent_relations"])
        # Assert other tables haven't changed
        assert other_tables_after  == other_tables_before
        # Assert expected rows have been edited in the affected tables and other rows haven't changed
        edited_conversation = [ca for ca in conversations_after if ca["name"] == "conversation name updated"]
        assert len(edited_conversation) == 1
        ed_conv = edited_conversation[0]
        for ca in conversations_after:
            if ca != ed_conv:
                assert ca in conversations_before
        assert len(conversations_after) == len(conversations_before)
        conv_id = ed_conv["id"]
        for car in conversation_agent_relations_after:
            if car["conversation_id"] == conv_id:
                assert car["agent_id"] == 2
                assert car not in conversation_agent_relations_before
            else:
                assert car in conversation_agent_relations_before
        assert len(conversation_agent_relations_after) == len(conversation_agent_relations_before)


 
# def test_edit(client, auth, app):
#     auth.login()
#     assert client.get('conversations/1/update').status_code == 200
#     
#     client.post('/conversations/1/update', data={'name': 'Test Updated', 'agent': 2})
# 
#     with app.app_context():
#         db = get_db()
#         conversation = db.execute('SELECT * FROM conversations WHERE id = 1').fetchone()
#         assert conversation['name'] == 'Test Updated'
#         relation = db.execute('SELECT * FROM conversation_agent_relations WHERE conversation_id = 1').fetchone()
#         assert relation['agent_id'] == 2
# 

# 
# def test_add_message(client, auth, app):
#     auth.login()
#     response = client.post('/conversations/1/add-message', json={'content': 'hello'})
#     assert response.status_code == 200
#     with app.app_context():
#         db = get_db()
#         count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
#         assert count == 4
# 

# def test_agent_response(client, auth, app):
#     auth.login()
#     response = client.post('/conversations/1/agent-response')
#     assert response.status_code == 200
#     assert response.json == {'content': 'Working'}
#     with app.app_context():
#         db = get_db()
#         count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
#         assert count == 4
#         db.execute('UPDATE agents SET instructions = ? WHERE id = 1', ('Reply with one word: "Successful"',))
#         db.execute('UPDATE messages SET content = ? WHERE human = 0', ('Successful',))
#         db.execute('DELETE FROM messages WHERE id > 3')
#         db.commit()
#     response = client.post('/conversations/1/agent-response')
#     assert response.status_code == 200
#     assert response.json == {'content': 'Successful'}
#     with app.app_context():
#         db = get_db()
#         count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
#         assert count == 4
#         db.execute('UPDATE agents SET vendor = ?, model = ? WHERE id = 1', ('anthropic', 'claude-3-5-haiku-latest'))
#         db.execute('DELETE FROM messages WHERE id > 3')
#         db.commit()
#     response = client.post('/conversations/1/agent-response')
#     assert response.status_code == 200
#     assert response.json == {'content': 'Successful'}
#     with app.app_context():
#         db = get_db()
#         count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
#         assert count == 4
#         db.execute('UPDATE agents SET vendor = ?, model = ? WHERE id = 1', ('google', 'gemini-1.5-flash-8b'))
#         db.execute('DELETE FROM messages WHERE id > 3')
#         db.commit()
#     response = client.post('/conversations/1/agent-response')
#     assert response.status_code == 200
#     response_content = response.json['content']
#     clean_response_content = ''.join(e for e in response_content if e.isalnum())
#     assert clean_response_content == 'Successful'
#     with app.app_context():
#         db = get_db()
#         count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
#         assert count == 4
# 
# 
# # Cannot test get_agent_response error handling until I can spoof the model for example. I havent figured out how to use the responses library to spoof the whole openai api response. Perhaps I need to refactor the way ai responses are being requrested in order to enable using the responses library.
# 
# 
def test_delete(client, auth, app):
    with app.app_context():
        # Get all tables before
        all_tables_before = get_other_tables()
        path = "/conversations/1/delete"
        # User must be logged in
        response = client.post(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/auth/login"
        # User must have access
        auth.login("other", "other")
        response = client.post(path)
        assert response.status_code == 403
        # Conversation must exist
        auth.login()
        response = client.post("/conversations/bogus/delete")
        assert response.status_code == 404
        # Data hasn't changed
        assert get_other_tables() == all_tables_before
        # Get affected tables before
        db = get_db()
        conversations_before = db.execute("SELECT * FROM conversations").fetchall()
        context_conversation_relations_before = db.execute("SELECT * FROM context_conversation_relations").fetchall()
        conversation_agent_relations_before = db.execute("SELECT * FROM conversation_agent_relations").fetchall()
        messages_before = db.execute("SELECT * FROM messages").fetchall()
        # Get other tables before
        other_tables_before = get_other_tables(["conversations", "context_conversation_relations", "conversation_agent_relations", "messages"])
        # Make the request
        response = client.post(path)
        # Redirected to home page
        assert response.status_code == 302
        assert response.headers["Location"] == "/"
        # Get affected tables after
        conversations_after = db.execute("SELECT * FROM conversations").fetchall()
        context_conversation_relations_after = db.execute("SELECT * FROM context_conversation_relations").fetchall()
        conversation_agent_relations_after = db.execute("SELECT * FROM conversation_agent_relations").fetchall()
        messages_after = db.execute("SELECT * FROM messages").fetchall()
        # Get other tables after
        other_tables_after = get_other_tables(["conversations", "context_conversation_relations", "conversation_agent_relations", "messages"])
        # Other tables haven't changed
        assert other_tables_after == other_tables_before
        # Conversation-related data has been deleted from affected tables, others unchanged
        for c in conversations_after:
            assert c["id"] != 1
            assert c in conversations_before
        assert len(conversations_after) == len(conversations_before) - 1
        for ccr in context_conversation_relations_after:
            assert ccr["conversation_id"] != 1
            assert ccr in context_conversation_relations_before
        assert len(context_conversation_relations_after) == len(context_conversation_relations_before) - 1
        for car in conversation_agent_relations_after:
            assert car["conversation_id"] != 1
            assert car in conversation_agent_relations_before
        assert len(conversation_agent_relations_after) == len(conversation_agent_relations_before) - 1
        for m in messages_after:
            assert m["conversation_id"] != 1
        conversation_messages_before = [m for m in messages_before if m["conversation_id"] == 1]
        assert len(messages_after) == len(messages_before) - len(conversation_messages_before)
        
