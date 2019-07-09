'''A very basic ORM for todos and users.

This module implements a very limited ORM that wraps the Todo and User tables
in simple classes and uses specific request functions to retrieve the data and
return lists of classes or singular classes.
'''

import json

from flask import g

class OrmObject(object):
    '''Base class for ORM objects'''

    # The name of the table to retrieve data from
    TABLE = None # type: str

    def _get_field_names(self):
        # type: () -> List[str]
        '''Get the field/column names for the object based on the class's
        properties.
        '''

        self_type = type(self)
        fields = [prop_name for prop_name in dir(self)
                  if hasattr(self_type, prop_name)
                  and isinstance(getattr(self_type, prop_name), property)]

        return fields

    def keys(self):
        # type: () -> List[str]
        '''Implementing the mapping protocol to allow conversion to a dict'''
        return self._get_field_names()

    def __getitem__(self, key):
        # type: (str) -> Any
        '''Implementing the mapping protocol to allow conversion to a dict'''
        if key not in self.keys():
            raise KeyError(key)
        return getattr(self, key)

    def _populate_fields(self):
        # type: () -> None
        '''Populate fields after fetching data from the database'''

        field_names = ', '.join(self._get_field_names())

        command = "SELECT {field_names} FROM {table} WHERE id = {id_}"
        command = command.format(field_names=field_names,
                                 table=self.TABLE,
                                 id_=self.id)

        cur = g.db.execute(command)
        row = cur.fetchone()

        for key, value in dict(row).items():
            setattr(self, '_' + key, value)

    def _set(self, field, value):
        # type: (str, Any) -> None
        '''Set the value and in the database and then on the class instance. If
        the instance value is the same as the passed value, do nothing.'''

        if getattr(self, field) == value:
            return

        command = "UPDATE {table} SET {field} = {value} WHERE id = {id_}"
        command = command.format(table=self.TABLE,
                                 field=field,
                                 value=value,
                                 id_=self.id)

        g.db.execute(command)
        g.db.commit()
        setattr(self, '_' + field, value)

    def to_json(self):
        # type: () -> str
        '''Return a json string version of this class'''
        return json.dumps(dict(self))


class Todo(OrmObject):
    '''The todo wrapper class'''

    TABLE = 'todos'

    def __init__(self, id, user_id=None, description=None, completed=None):
        self._id = id
        self._user_id = user_id
        self._description = description
        self._completed = completed

    @property
    def id(self):
        return self._id

    @property
    def user_id(self):
        if self._user_id is None:
            self._populate_fields()

        return self._user_id

    @property
    def description(self):
        if self._description is None:
            self._populate_fields()

        return self._description

    @description.setter
    def description(self, value):
        self._set('description', value)

    @property
    def completed(self):
        if self._completed is None:
            self._populate_fields()

        return bool(self._completed)

    @completed.setter
    def completed(self, value):
        self._set('completed', int(value))


class User(OrmObject):
    '''The user wrapper class'''

    TABLE = 'users'

    def __init__(self, id, username=None):
        self._id = id
        self._username = username

    @property
    def id(self):
        return self._id

    @property
    def username(self):
        if self._username is None:
            self._populate_fields()

        return self._username


def get_user(username, password):
    command = "SELECT * FROM users" \
              " WHERE username = '{username}' AND password = '{password}'"

    command = command.format(username=username, password=password)

    cur = g.db.execute(command)
    row = cur.fetchone()
    if not row:
        return None

    return User(row['id'], username=row['username'])


def get_todo_count():
    cur = g.db.execute("SELECT COUNT(*) FROM todos")
    return cur.fetchone()[0]


def get_todos(offset=0, limit=None):
    command = "SELECT * FROM todos" \
              " ORDER BY id"

    if limit is not None:
        command += " LIMIT {limit} OFFSET {offset}".format(limit=limit, offset=offset)

    cur = g.db.execute(command)

    todos = []
    for row in cur.fetchall():
        todo_kwargs = dict(row)
        todos.append(Todo(**todo_kwargs))

    return todos


def get_todo(id_):
    return Todo(id=id_)


def add_todo(user_id, description):

    command = "INSERT INTO todos (user_id, description)" \
              " VALUES ({user_id}, '{description}')"

    command = command.format(user_id=user_id, description=description)

    g.db.execute(command)
    g.db.commit()


def delete_todo(id_):
    select_command = "SELECT * FROM todos WHERE id = {id_}".format(id_=id_)
    cur = g.db.execute(select_command)
    row = cur.fetchone()
    if not row:
        return

    delete_command = "DELETE FROM todos WHERE id = {id_}".format(id_=id_)
    g.db.execute(delete_command)
    g.db.commit()

