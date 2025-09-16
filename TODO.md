# TODO

- [x] Merge just-contexts with masters-with-lists-and-agents
- [x] Define user stories
- [x] Update the schema
- [ ] Write the requirements and tests along with them as you go.

## Requirements

- [ ] Make it work. Don't worry about the code being good or fast at this stage.

- [x] Lists is working perfectly
- [x] Tests for lists are complete
- [x] Agents is working perfectly
- [x] Tests for agents are complete
- [x] Contexts is working perfectly (see points below)
- [x] Tests for contexts are complete

- [ ] You can add a name and description to a tethered list.
    - [x] There's a "name" field and a description field on the new tethered list form.
    - [x] On the tethered lists's view layout it indicated that it's a tethered list and there's a link to view the master list.
    - [x] The list index shows name of list not name of master list.
    - [x] The route to edit tethered lists is not blocked, and you can edit the name and description.
    - [ ] Update tests
        - [ ] Cover the above changes
            - [ ] Don't forget deleting a tethered list
        - [ ] Add a test for when you add an item to a master list: it should show in the tethered list view layout.
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
    - [ ] List view layouts have links to their related contexts.
- [x] You can add as many lists as you want.
- [x] You can add an agent to a context if you own the context and the agent.
    - [x] You can't add a tethered agent. For now. I need to fix it so that tethered agents don't have their own table. That means redoing some of how agents works.
    - [x] If there are no related agents it says "Empty"
    - [x] There's a button on the context view layout to add an agent
    - [x] The agent name and description are shown in the context.
    - [x] Once an agent has been added there is a button to remove it.
    - [x] There is a button to view the agent.
    - [ ] Agent view layouts have links to their related contexts.
- [x] You can add as many agents as you want.
- [ ] Deleting a context will delete its list relations agent relation (if exists)
- [x] Contexts uses "new" and "edit" nomenclature not "create" and "update"
- [ ] Optimization:Sanitize user lists (lists.py::get_user_lists()) such that master list names are replaced immediately, and not later in the route function. 
    - [ ] Affects lists/index layout and contexts/new_list layout and maybe others
- [ ] Master lists view have links to all lists which are tethered to it and owned by the user.
- [ ] Test working with edge cases
    - [ ] tethering to a master list with no items
    - [ ] tethering to a master list with no details
- [ ] All ids have a prefix based on the table it belongs to
- [ ] Remove master agents and master lists
- [ ] Make agent descriptions not required
- [ ] Improve agent model id validation to only accept available ids
- [ ] Fix data validation tests. checking the flash error text in response.data is giving false positives. test_agents.py::test_new_post it's saying description is required when it's not (it is on the front end but not on the back end.). Applies to all data validation tests including lists and contexts (new and edit) (post requests) (You could use specific messages for each field.
- [ ] Remove all explanatory comments
- [ ] Remove db.row_factory = dict_factory as it's configured in get_db() now
- [ ] Replace ' with " everywhere
