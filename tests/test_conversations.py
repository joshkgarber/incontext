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
        data["agent_id"] == "1"
        response = client.post(path, data=data)
        assert b"Name and agent are required" in response.data
        assert get_other_tables() == all_tables_before
        # Agent ID
        data["agent_id"] == ""
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


# def test_view_conversation(app, client, auth):
#     # user must be logged in
#     response = client.get('/conversations/1', follow_redirects=True)
#     assert b'Log In' in response.data
#     assert b'Register' in response.data
#     
#     auth.login()
# 
#     # conversation must exist
#     assert client.get('conversations/2').status_code == 404
#     
#     # serve conversation page to to user who created it (default test data complies)
#     response = client.get('/conversations/1')
#     assert response.status_code == 200
#     assert b'Log Out' in response.data
#     assert b'Conversation "test name"' in response.data
#     assert b'href="/conversations/1/update"' in response.data
#     assert b'Name: Test' in response.data
#     assert b'Model: gpt-4.1-mini' in response.data
#     assert b'Role: Testing Agent' in response.data
#     assert b'Instructions: Reply with one word: &#34;Working&#34;.' in response.data
#     assert b'This is a test.' in response.data
#     assert b'Working' in response.data
#     
#     # forbid conv page to non-creator user
#     with app.app_context():
#         db = get_db()
#         db.execute('UPDATE conversations SET creator_id = 3 WHERE id = 1')
#         db.commit()
#     assert client.get('/conversations/1').status_code == 403
# 
# 
# def test_update_conversation(client, auth, app):
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
# @pytest.mark.parametrize('path', (
#     '/conversations/create',
#     '/conversations/1/update',
# ))
# def test_create_update_validate(client, auth, path):
#     auth.login()
#     response = client.post(path, data={'name': '', 'agent': 1})
#     assert b'Name and agent are required.' in response.data
#     response = client.post(path, data={'name': 'test', 'agent': ''})
#     assert b'Name and agent are required' in response.data
# 
# 
# @pytest.mark.parametrize('path', (
#     'conversations/create',
#     'conversations/1/update',
#     'conversations/1/delete',
#     'conversations/1/add-message',
#     'conversations/1/agent-response',
# ))
# def test_modify_conversation_login_required(client, path):
#     response = client.post(path)
#     assert response.headers['Location'] == '/auth/login'
# 
# 
# @pytest.mark.parametrize('path', (
#     'conversations/2/update',
#     'conversations/2/delete',
#     'conversations/2/add-message',
#     'conversations/2/agent-response',
# ))
# def test_modify_conversation_must_exist(client, auth, path):
#     auth.login()
#     assert client.post(path).status_code == 404
# 
# 
# def test_modify_conversation_must_be_creator(app, client, auth):
#     # change the conversation creator to another user
#     with app.app_context():
#         db = get_db()
#         db.execute('UPDATE conversations SET creator_id = 3 WHERE id = 1')
#         db.commit()
# 
#     auth.login()
#     # current user doesn't see Open link
#     assert b'href="/conversations/1"' not in client.get('/conversations').data
#     # current user can't view or modify another user's conversation
#     assert client.post('conversations/1/update').status_code == 403
#     assert client.post('conversations/1/delete').status_code == 403
#     assert client.post('conversations/1/add-message').status_code == 403
#     assert client.post('conversations/1/agent-response').status_code == 403
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
# 
# def test_add_message_validation(client, auth, app):
#     auth.login()
#     response = client.post('/conversations/1/add-message', json={'content': ''})
#     assert b'Message can\'t be empty.' in response.data
# 
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
# def test_delete(client, auth, app): # the delete view should should redirect to the index url and the conversation should no longer exist in the db.
#     auth.login()
#     response = client.post('/conversations/1/delete')
#     assert response.headers['Location'] == '/conversations/'
#     with app.app_context():
#         db = get_db()
#         conversation = db.execute('SELECT * FROM conversations WHERE id = 1').fetchone()
#         assert conversation is None
#         # messages whould be deleted
#         count = db.execute('SELECT COUNT(id) FROM messages WHERE conversation_id = 1').fetchone()[0]
#         assert count == 0
