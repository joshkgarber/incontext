# TODO

- [x] Merge just-conversations with this project
- [x] Define requirements
- [ ] Write the code and tests along with them as you go.
- [ ] Run a coverage report
- [ ] Deploy

## Requirements

- [ ] Conversations are had on the context view
- [ ] Conversations are on the left, lists are on the right
- [ ] Contexts don't have connected agents anymore. Only the conversation does.
- [x] Contexts/new-conversation: You create a conversation from the context. You have to choose an agent.
    - [x] Tests
- [ ] Conversation index shows for each conversation:
    - [x] conversation name
    - [x] link to edit (see below)
    - [x] related agent and link to view
    - [x] related context and link to view
    - [x] Tests
- [ ] Conversations/edit: You can change the name, related agent, and related context.
- [ ] There's no view route for the conversation. You can only view it in the context.
- [ ] You can delete a conversation, but you can't just remove it from a context. I.e. a conversation cannot exist without a context.
- [ ] Remove creator id from context_list_relations and context_agent_relations
- [ ] Update the tests for contexts
- [ ] Agent view: should show related conversations with a link to the conversation and a link to the related context
- [ ] Make it work. Don't worry about the code being good or fast at this stage.
