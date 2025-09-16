# TODO

- [x] Merge just-contexts with masters-with-lists-and-agents
- [x] Define user stories
- [x] Update the schema
- [x] Write the requirements and tests along with them as you go.
- [x] Run a coverage report
- [x] Deploy

## Requirements

- [x] Make it work. Don't worry about the code being good or fast at this stage.

- [x] Lists is working perfectly
- [x] Tests for lists are complete
- [x] Agents is working perfectly
- [x] Tests for agents are complete
- [x] Contexts is working perfectly (see points below)
- [x] Tests for contexts are complete

- [x] You must be logged in to view contexts (update layout needed)
- [x] You can only view contexts which you own.
- [x] Contexts have a view template
    - [x] Name, description, creator and created, related lists and agents
- [x] You can add a list to a context (not a master list) if you own the context and you own the list.
    - [x] If there are no related lists it says "Empty"
    - [x] There's a button on the context view layout to add a list
    - [x] The list name and description are shown in the context.
    - [x] Once a list has been added there is a button to remove the list
    - [x] There is a button to view the list
    - [x] List view layouts have links to their related contexts.
- [x] You can add as many lists as you want.
- [x] You can add an agent to a context if you own the context and the agent.
    - [x] You can't add a tethered agent. For now. I need to fix it so that tethered agents don't have their own table. That means redoing some of how agents works.
    - [x] If there are no related agents it says "Empty"
    - [x] There's a button on the context view layout to add an agent
    - [x] The agent name and description are shown in the context.
    - [x] Once an agent has been added there is a button to remove it.
    - [x] There is a button to view the agent.
    - [x] Agent view layouts have links to their related contexts.
- [x] You can add as many agents as you want.
- [x] Deleting a context will delete its list relations agent relation (if exists)
- [x] Contexts uses "new" and "edit" nomenclature not "create" and "update"
- [x] Remove master agents and master lists
