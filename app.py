import os

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, text, delete, insert
from sqlalchemy.sql.expression import update, select

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure Application
app = Flask(__name__)

# Ensure templates are auto reloded
app.config["TEMPLATES_AUTO_RELOD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Making connection to the database
engine = create_engine("sqlite:///data.db", echo = False, connect_args={"check_same_thread": False})
conn = engine.connect()

# Make Tables:
meta = MetaData()
users = Table(
    'users', meta,
    Column('id', Integer, primary_key = True),
    Column('username', Text),
    Column('hash', Text),
    Column('phone', Text),
    Column('aadhaar', Text)
)

meta.create_all(engine)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    if session['user_id']:
        return render_template('index.html')
    return render_template('login.html')

# Login and Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Forget any user id
    session.clear()

    if request.method == 'GET':
        return render_template('register.html')
    
    # Data at the time of register
    username = request.form.get('username')
    password = request.form.get('password')
    re_password = request.form.get('re_password')
    if password != re_password:
        return render_template('apology.html', 'Passwords don\'t match')
    phone = request.form.get('phone')

    user = text('SELECT phone FROM users GROUP BY id')
    result = conn.execute(user)
    res = []
    for row in result:
        res.append(row[0])
    if phone in res:
        return render_template('apology.html', txt='This phone no. is already registered!, Try to login with this no. of register with another no.')
    
    ins = users.insert().values(username = username, hash = generate_password_hash(password), phone = phone, aadhaar = None)
    conn.execute(ins)

    session['user_id'] = id

    return render_template('index.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Forget any user id
    session.clear()

    if request.method == 'GET':
        return render_template('login.html')
    
    # Data at the time of register
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = text('SELECT username, hash, id FROM users')
    result = conn.execute(user)
    for row in result:
        if row[0] == username and check_password_hash(row[1], password):
            session['user_id'] = row[2]
            return render_template('index.html')
    
    return render_template('apology.html', txt = 'Login Error!')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # get data from table
    query = users.select().where(id == session['user_id'])
    results = conn.execute(query)
    cred = ()
    for i in results:
        cred = i
    name_t = cred[1]
    phone_t = cred[3]
    aadhaar_t = cred[4]

    if request.method == 'GET':
        return render_template('profile.html', name=name_t, phone=phone_t, aadhaar=aadhaar_t)
    
    # get data from form
    name = request.form.get('username')
    if name == '':
        name = name_t
    phone = request.form.get('phone')
    if phone == '':
        phone = phone_t
    aadhaar = request.form.get('aadhaar')
    if aadhaar == '':
        aadhaar = aadhaar_t

    # Implementation of the Logic
    update = users.update().values(username=name, phone=phone, aadhaar=aadhaar).where(id == session['user_id'])
    conn.execute(update)

    return render_template('profile.html', name=name, phone=phone, aadhaar=aadhaar)
