DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS contexts;
DROP TABLE IF EXISTS context_list_relations;
DROP TABLE IF EXISTS context_agent_relations;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS details;
DROP TABLE IF EXISTS item_detail_relations;
DROP TABLE IF EXISTS lists;
DROP TABLE IF EXISTS list_item_relations;
DROP TABLE IF EXISTS list_detail_relations;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS agent_models;


CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    admin BOOL NOT NULL DEFAULT 0
);


CREATE TABLE contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users (id)
);


CREATE TABLE context_list_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    list_id INTEGER NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users (id),
    FOREIGN KEY (context_id) REFERENCES contexts (id),
    FOREIGN KEY (list_id) REFERENCES lists (id)
);


CREATE TABLE context_agent_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users (id),
    FOREIGN KEY (context_id) REFERENCES contexts (id),
    FOREIGN KEY (agent_id) REFERENCES agents (id)
);


CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users (id)
);


CREATE TABLE details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (creator_id) REFERENCES users (id)
);


CREATE TABLE item_detail_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    detail_id INTEGER NOT NULL,
    content TEXT,
    FOREIGN KEY (item_id) REFERENCES items (id)
    FOREIGN KEY (detail_id) REFERENCES details (id)
);


CREATE TABLE lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (creator_id) REFERENCES users (id)
);


CREATE TABLE list_item_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    FOREIGN KEY (list_id) REFERENCES lists (id),
    FOREIGN KEY (item_id) REFERENCES items (id)
);


CREATE TABLE list_detail_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    detail_id INTEGER NOT NULL,
    FOREIGN KEY (list_id) REFERENCES lists (id),
    FOREIGN KEY (detail_id) REFERENCES details (id)
);


CREATE TABLE agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    model_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    instructions TEXT NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users (id),
    FOREIGN KEY (model_id) REFERENCES agent_models (id)
);


CREATE TABLE agent_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    provider_code TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_code TEXT NOT NULL,
    model_description TEXT NOT NULL
);

