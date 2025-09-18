# TODO

- [x] Merge just-conversations with this project
- [x] Define requirements
- [ ] Write the code and tests along with them as you go.
- [ ] Run a coverage report
- [ ] Deploy

## Requirements

- [x] Conversations are had on the context view
- [x] Conversations are on the left, lists are on the right
- [x] Contexts don't have connected agents anymore. Only the conversation does.
- [x] Contexts/new-conversation: You create a conversation from the context. You have to choose an agent.
    - [x] Tests
- [x] Conversation index shows for each conversation:
    - [x] conversation name
    - [x] link to edit (see below)
    - [x] related agent and link to view
    - [x] related context and link to view
    - [x] Tests
- [x] There's no view route for the conversation. You can only view it in the context.
- [x] Conversations/edit: You can change the name, related agent, and related context.
    - [x] Tests
- [x] Remove creator id from context_list_relations
- [ ] Agent view: should show related conversations with a link to the conversation and a link to the related context. also a list of all the contexts alone.
    - [x] Code
    - [ ] Tests
- [ ] Full conversation usage on context view page
    - [ ] Migrate code from the conversation view template
- [ ] You can delete a conversation, but you can't just remove it from a context. I.e. a conversation cannot exist without a context.
    - [ ] You can delete a conversation at the edit screen.
    - [ ] Tests
- [ ] Make it work. Don't worry about the code being good or fast at this stage.
