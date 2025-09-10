# TODO

- [x] Merge just-contexts with masters-with-lists-and-agents
- [x] Define user stories
- [x] Update the schema
- [ ] Write the user stories and tests along with them as you go.

## User stories

- [x] You must be logged in to view contexts (update layout needed)
- [x] You can only view contexts which you own.
- [x] Contexts have a view template
    - [x] Name, description, creator and created, related lists and agents
- [ ] You can add a list to a context (not a master list) if you own the context and you own the list.
    - [ ] There's a button on the context view layout to add a list
    - [ ] The list name and description are shown in the context.
    - [ ] Once a list has been added there is a button to remove the list
    - [ ] There is a button to view the list
    - [ ] List view layouts have links to their related contexts.
- [ ] You can add as many lists as you want.
- [ ] You can add an agent to a context if you own the context and the agent.
    - [ ] The agent name and description are shown in the context.
    - [ ] There's a button on the context view layout to add an agent
    - [ ] Once an agent has been added there is a button to remove it.
    - [ ] There is a button to view the agent.
    - [ ] Agent view layouts have links to their related contexts.
- [ ] You can add as many agents as you want.
- [ ] Deleting a context will delete its list relations agent relation (if exists)
- [ ] Contexts uses "new" and "edit" nomenclature not "create" and "update"
