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

from . import orm


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

    user = orm.get_user(username, password)
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
    todo = orm.get_todo(id)
    return render_template('todo.html', todo=todo)


@app.route('/todo/<id>/json', methods=['GET'])
def todo_json(id):
    todo = orm.get_todo(id)
    return todo.to_json()


@app.route('/todo', methods=['GET'])
@app.route('/todo/', methods=['GET'])
def todos():
    if not session.get('logged_in'):
        return redirect('/login')

    todos = orm.get_todos()

    return render_template('todos.html', todos=todos)


@app.route('/todo/page/<int:page>', methods=['GET'])
def todos_paginated(page):
    if not session.get('logged_in'):
        return redirect('/login')

    page_size = 5

    count = orm.get_todo_count()

    page_count = count / page_size 
    remainder = count % page_size != 0
    max_page = page_count + int(remainder) 

    page = page if page < max_page else max_page
    offset = page_size * (page - 1)

    todos = orm.get_todos(offset=offset, limit=page_size)

    return render_template('todos.html', todos=todos, page=page, max_page=max_page)


@app.route('/todo', methods=['POST'])
@app.route('/todo/', methods=['POST'])
def todos_POST():
    if not session.get('logged_in'):
        return redirect('/login')

    description = request.form.get('description', '')

    if description:
        orm.add_todo(session['user']['id'], description)

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
    todo = orm.get_todo(id)
    todo.completed = completed
    return json.dumps({'id': id, 'completed': completed})


@app.route('/todo/<id>', methods=['POST'])
def todo_delete(id):
    if not session.get('logged_in'):
        return redirect('/login')

    orm.delete_todo(id)

    flash("Todo item deleted!")

    return redirect('/todo')

