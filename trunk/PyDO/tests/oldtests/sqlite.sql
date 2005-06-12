CREATE TABLE pydogroup (
   id INTEGER NOT NULL PRIMARY KEY,
   groupname TEXT UNIQUE NOT NULL
);

CREATE TABLE pydouser (
   id INTEGER NOT NULL PRIMARY KEY,
   firstname TEXT,
   lastname TEXT
);

CREATE TABLE pydouser_pydogroup (
   user_id INTEGER NOT NULL REFERENCES pydouser,
   group_id INTEGER NOT NULL REFERENCES pydogroup,
   PRIMARY KEY(user_id, group_id)
);

CREATE TABLE article (
   id INTEGER NOT NULL PRIMARY KEY,
   title TEXT NOT NULL,
   body TEXT NOT NULL,
   creator INTEGER NOT NULL REFERENCES pydouser,
   created TIMESTAMP NOT NULL
);



