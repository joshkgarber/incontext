INSERT INTO users (username, password, admin)
VALUES
  ("test", "scrypt:32768:8:1$JinXM6T6WFsqjrFf$fd71d2efa642467a90fd934b62e8517ae073cb85acf8729fa16b5d226823683e77b9c634d92bafa90fb2b1e437fb18a0d00b38bed96c9b211fe1610f638f2bfa", 1),
  ("other", "pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79", 0),
  ("admin2", "scrypt:32768:8:1$huAZd2BbgeBRZ1C6$780368ac6f62cfd8fa4c4505430d48f4a8366fcfda4c14797acd011691176a13ea7c5c6671f8d04793f430a86a54a26d3a49c624d62d9d4210608a70cb0151da", 1);


INSERT INTO contexts (creator_id, name, description)
VALUES
	(2, "context name 1", "context description 1"),
	(2, "context name 2", "context description 2"),
	(3, "context name 3", "context description 3");


INSERT INTO context_list_relations (creator_id, context_id, list_id)
VALUES
    (2, 1, 1),
    (2, 1, 2),
    (2, 1, 5);


INSERT INTO master_lists (creator_id, name, description)
VALUES
    (2, "master list name 1", "master list description 1"),
    (2, "master list name 2", "master list description 2");


INSERT INTO master_items (creator_id, name)
VALUES
	(2, "master item name 1"),
	(2, "master item name 2"),
	(2, "master item name 3");


INSERT INTO master_details (creator_id, name, description)
VALUES
	(2, "master detail name 1", "master detail description 1"),
	(2, "master detail name 2", "master detail description 2"),
	(2, "master detail name 3", "master detail description 3");


INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, master_content)
VALUES
	(1, 1, "master relation content 1"),
	(1, 2, "master relation content 2"),
	(2, 1, "master relation content 3"),
	(2, 2, "master relation content 4"),
	(3, 3, "master relation content 5");


INSERT INTO master_list_item_relations (master_list_id, master_item_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3);


INSERT INTO master_list_detail_relations (master_list_id, master_detail_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3);


INSERT INTO items (creator_id, name)
VALUES
	(2, "item name 1"),
	(2, "item name 2"),
	(2, "item name 3"),
	(3, "item name 4"),
	(3, "item name 5"),
	(3, "item name 6"),
    (2, "item name 7"),
    (2, "item name 8"),
    (2, "item name 9");


INSERT INTO details (creator_id, name, description)
VALUES
	(2, "detail name 1", "detail description 1"),
	(2, "detail name 2", "detail description 2"),
	(2, "detail name 3", "detail description 3"),
	(3, "detail name 4", "detail description 4"),
	(3, "detail name 5", "detail description 5"),
	(3, "detail name 6", "detail description 6");


INSERT INTO item_detail_relations (item_id, detail_id, content)
VALUES
	(1, 1, "relation content 1"),
	(1, 2, "relation content 2"),
	(2, 1, "relation content 3"),
	(2, 2, "relation content 4"),
	(3, 3, "relation content 5"),
	(4, 4, "relation content 6"),
	(4, 5, "relation content 7"),
	(5, 4, "relation content 8"),
	(5, 5, "relation content 9"),
	(6, 6, "relation content 10");


INSERT INTO lists (creator_id, name, description, tethered)
VALUES
	(2, "list name 1", "list description 1", 0),
	(2, "list name 2", "list description 2", 0),
	(3, "list name 3", "list description 3", 0),
	(3, "list name 4", "list description 4", 0),
    (2, "tethered list name 1", "tethered list description 1", 1),
    (2, "tethered list name 2", "tethered list description 2", 1),
    (3, "tethered list name 3", "tethered list description 3", 1);


INSERT INTO list_item_relations (list_id, item_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3),
	(3, 4),
	(3, 5),
	(4, 6),
    (5, 7),
	(6, 8),
	(7, 9);


INSERT INTO list_detail_relations (list_id, detail_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3),
	(3, 4),
	(3, 5),
	(4, 6);


INSERT INTO master_agents (creator_id, name, description, model_id, role, instructions)
VALUES
	(2, "master agent name 1", "master agent description 1", 3, "master agent role 1", "Reply with one word: Working"),
	(2, "master agent name 2", "master agent description 2", 6, "master agent role 2", "Reply with one word: Working"),
	(2, "master agent name 3", "master agent description 3", 9, "master agent role 3", "Reply with one word: Working");


INSERT INTO agents (creator_id, name, description, model_id, role, instructions)
VALUES
	(2, "agent name 1", "agent description 1", 3, "agent role 1", "agent instructions 1"),
	(2, "agent name 2", "agent description 2", 6, "agent role 2", "agent instructions 2"),
	(3, "agent name 3", "agent description 3", 9, "agent role 3", "agent instructions 3");


INSERT INTO tethered_agents (creator_id, master_agent_id)
VALUES
    (2, 1),
    (2, 2),
    (3, 3);


INSERT INTO list_tethers (list_id, master_list_id)
VALUES
    (5, 1),
    (6, 1),
    (7, 2);


INSERT INTO untethered_content (list_id, item_id, master_detail_id, content)
VALUES
    (5, 7, 1, "untethered content 1"),
    (5, 7, 2, "untethered content 2"),
    (6, 8, 1, "untethered content 3"),
    (6, 8, 2, "untethered content 4"),
    (7, 9, 3, "untethered content 5");

