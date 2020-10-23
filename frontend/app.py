from flask import Flask, render_template, request, session, redirect, flash
from werkzeug.security import check_password_hash, generate_password_hash
import pika
import messaging
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']


@app.route('/', methods=['GET', 'POST'])
def loginpage():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        msg = messaging.Messaging()
        msg.send('GETHASH', {'username': username})
        response = msg.receive()
        if response['success'] != True:
            return "Login failed."
        if check_password_hash(response['hash'], password):
            session['username'] = username
            return redirect('/userpage')
        else:
            return "Login failed."
    return render_template('login.html')


@app.route('/userpage', methods=['GET', 'POST'])
def userpage():
    if 'username' not in session:
        return redirect('/')
    if request.method == 'POST':
        dropdownvalue = request.form['dropdownvalue']
        searchfield = request.form['searchfield']
        msg = messaging.Messaging()
        msg.send(
            'SCRAPE',
            {
                'searchfield': searchfield,
                'dropdownvalue': dropdownvalue
            }
        )
        response = msg.receive()
        if response['success']:
            if response['search'] == 'cocktail_name':
                flash(response['cocktailname'])
                thumbnail = (response['cocktailimage'])
                return render_template('userpage.html', thumbnail=thumbnail)
            elif response['search'] == 'ingredient_name':
                flash(response['ingredientdescription'])
            elif response['search'] == 'random':
                flash(response['cocktailname'])
                thumbnail = (response['cocktailimage'])
                return render_template('userpage.html', thumbnail=thumbnail)
        else:
            flash("error")
        print(session['username'])
        username = session['username']
    return render_template('userpage.html', usernm=session['username'])


@app.route('/register', methods=['GET', 'POST'])
def registerpage():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirmpassword = request.form['confirmpassword']
        if password == confirmpassword:
            msg = messaging.Messaging()
            msg.send(
                'REGISTER',
                {
                    'firstname': firstname,
                    'lastname': lastname,
                    'email': email,
                    'username': username,
                    'hash': generate_password_hash(password)
                }
            )
            response = msg.receive()
            if response['success']:
                session['username'] = username
                return redirect('/userpage')
            else:
                return f"{response['message']}"
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')
