from flask import Flask, render_template, request, session, redirect
from werkzeug.security import check_password_hash, generate_password_hash
import pika
import messaging
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/', methods=['GET','POST'])
def loginpage():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        msg = messaging.Messaging()
        msg.send('GETHASH', { 'username': username })
        response = msg.receive()
        if response['success'] != True:
            return "Login failed."
        if check_password_hash(response['hash'], password):
            session['username'] = username
            return redirect('/userpage')
        else:
            return "Login failed."
    return render_template('login.html')

@app.route('/userpage', methods=['GET','POST'])
def userpage():
    if 'username' not in session:
        return redirect('/')
    cocktailname=None
    thumbnail=None
    category=None
    instructions=None
    ingredients=None
    measurements=None
    ingredientname=None
    ingredientdescription=None
    ingredienttype=None
    ingredientalchohol=None
    if request.method == 'POST':
        dropdownvalue = request.form['dropdownvalue']
        searchfield = request.form['searchfield']
        if dropdownvalue == 'cocktail_name' and searchfield == 'random':
            dropdownvalue = 'random'
        msg = messaging.Messaging()
        msg.send(
            'SCRAPE',
            {
                'searchfield' : searchfield,
                'dropdownvalue' : dropdownvalue
            }
        )
        response = msg.receive()
        if response['success']:
            if response['search'] == 'cocktail_name' or response['search'] == 'random':
                thumbnail = (response['cocktailimage'])
                cocktailname = (response['cocktailname'])
                category=(response['cocktailcategory'])
                instructions=(response['cocktailinstructions'])
                ingredients=(response['cocktailingredients'])
                measurements=(response['cocktailmeasurements'])
            elif response['search'] == 'ingredient_name':
                ingredientname= (response['ingredientname'])
                ingredientdescription= (response['ingredientdescription'])
                ingredienttype= (response['ingredienttype'])
                ingredientalchohol= (response['ingredientalchohol'])
        else:
            cocktailname = "ERROR"
    return render_template('userpage.html',thumbnail=thumbnail, cocktailname=cocktailname, category=category, instructions=instructions, ingredients=ingredients, measurements=measurements, ingredientname=ingredientname, ingredientdescription=ingredientdescription, ingredienttype=ingredienttype, ingredientalchohol=ingredientalchohol)

@app.route('/register', methods=['GET','POST'])
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
                    'firstname' : firstname,
                    'lastname' : lastname,
                    'email': email,
                    'username' : username,
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
