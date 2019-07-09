import json

from alayatodo import app
from flask import (
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    flash
    )


@app.route('/')
def home():
    with app.open_resource('../README.md', mode='r') as f:
        readme = "".join(l.decode('utf-8') for l in f)
        return render_template('index.html', readme=readme)


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_POST():
    username = request.form.get('username')
    password = request.form.get('password')

    sql = "SELECT * FROM users WHERE username = '%s' AND password = '%s'";
    cur = g.db.execute(sql % (username, password))
    user = cur.fetchone()
    if user:
        session['user'] = dict(user)
        session['logged_in'] = True
        return redirect('/todo')

    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    return redirect('/')


@app.route('/todo/<id>', methods=['GET'])
def todo(id):
    cur = g.db.execute("SELECT * FROM todos WHERE id ='%s'" % id)
    todo = cur.fetchone()
    return render_template('todo.html', todo=todo)

@app.route('/todo/<id>/json', methods=['GET'])
def todo_json(id):
    cur = g.db.execute("SELECT * FROM todos WHERE id ='%s'" % id)
    todo = cur.fetchone()
    todo_dict = dict([(k, todo[k]) for k in todo.keys()])
    return json.dumps(todo_dict)

@app.route('/todo', methods=['GET'])
@app.route('/todo/', methods=['GET'])
def todos():
    if not session.get('logged_in'):
        return redirect('/login')
    cur = g.db.execute("SELECT * FROM todos")
    todos = cur.fetchall()
    return render_template('todos.html', todos=todos)


@app.route('/todo/page/<int:page>', methods=['GET'])
def todos_paginated(page):
    if not session.get('logged_in'):
        return redirect('/login')

    page_size = 5

    cur = g.db.execute("SELECT COUNT(*) FROM todos")
    count = cur.fetchone()[0]

    max_page = count / page_size + 1
    page = page if page < max_page else max_page
    offset = page_size * (page - 1)

    command = "SELECT * FROM todos" \
              " ORDER BY id" \
              " LIMIT {page_size}" \
              " OFFSET {offset}".format(page_size=page_size, offset=offset)
    cur = g.db.execute(command)
    todos = cur.fetchall()

    return render_template('todos.html', todos=todos, page=page, max_page=max_page)


@app.route('/todo', methods=['POST'])
@app.route('/todo/', methods=['POST'])
def todos_POST():
    if not session.get('logged_in'):
        return redirect('/login')

    description = request.form.get('description', '')

    if description:
        g.db.execute(
            "INSERT INTO todos (user_id, description) VALUES ('%s', '%s')"
            % (session['user']['id'], request.form.get('description', ''))
        )
        g.db.commit()
    else:
        flash("You must provide a description.", "error")

    confirm_message = \
        "Todo item '{description}' added for user {user}!".format(
        description=description,
        user=session['user']['username'])

    flash(confirm_message)

    return redirect(url_for('todos'))


@app.route('/todo/<id>/complete', methods=['POST'])
def todo_complete(id):
    completed = int(request.form.get('completed'))
    g.db.execute(
        "UPDATE todos SET completed = {completed} WHERE id = {id_}".format(id_=id, completed=completed)
    )
    g.db.commit()
    return json.dumps({'id': id, 'completed': completed})


@app.route('/todo/<id>', methods=['POST'])
def todo_delete(id):
    if not session.get('logged_in'):
        return redirect('/login')

    cur = g.db.execute("SELECT * FROM todos WHERE id ='%s'" % id)
    todo = cur.fetchone()

    g.db.execute("DELETE FROM todos WHERE id ='%s'" % id)
    g.db.commit()

    confirm_message = \
        "Todo item '{description}' deleted!".format(
        description=todo['description'])

    flash(confirm_message)

    return redirect('/todo')

