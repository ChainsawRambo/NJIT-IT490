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
            session['cocktailname'] = None
            session['thumbnail'] = None
            session['category']=None
            session['instructions']=None
            session['ingredients']=None
            session['measurements']=None
            session['ingredientname']=None
            session['ingredientdescription']=None
            session['ingredienttype']=None
            session['ingredientalchohol']=None
            session['favorite']=False
            return redirect('/userpage')
        else:
            return "Login failed."
    return render_template('login.html')

@app.route('/userpage', methods=['GET','POST'])
def userpage():
    if 'username' not in session:
        return redirect('/')

    if request.method == 'POST':
        if 'btn2' in request.form:
            if session['cocktailname'] != None:
                msg = messaging.Messaging()
                msg.send(
                    'favorite',
                    {
                        'username' : session['username'],
                        'fav' : session['cocktailname']
                    }
                )
                response = msg.receive()
                if response['success']:
                    if response['deleted']:
                        session['favorite']=False
                    elif response['inserted']:
                        session['favorite']=True

        if 'btn1' in request.form:
            dropdownvalue = request.form['dropdownvalue']
            searchfield = request.form['searchfield']
            if dropdownvalue == 'cocktail_name' and searchfield == 'random':
                dropdownvalue = 'random'
            msg = messaging.Messaging()
            msg.send(
                'SCRAPE',
                {
                    'searchfield' : searchfield,
                    'dropdownvalue' : dropdownvalue,
                    'username' : session['username']
                }
            )
            response = msg.receive()
            if response['success']:
                if response['search'] == 'cocktail_name' or response['search'] == 'random':
                    session['thumbnail'] = (response['cocktailimage'])
                    session['cocktailname'] = (response['cocktailname'])
                    session['category']=(response['cocktailcategory'])
                    session['instructions']=(response['cocktailinstructions'])
                    session['ingredients']=(response['cocktailingredients'])
                    session['measurements']=(response['cocktailmeasurements'])
                    session['favorite'] = (response['favorite'])
                    session['ingredientname']=None
                    session['ingredientdescription']=None
                    session['ingredienttype']=None
                    session['ingredientalchohol']=None
                elif response['search'] == 'ingredient_name':
                    session['cocktailname']=None
                    session['thumbnail']=None
                    session['category']=None
                    session['instructions']=None
                    session['ingredients']=None
                    session['measurements']=None
                    session['ingredientname']= (response['ingredientname'])
                    session['ingredientdescription'] = (response['ingredientdescription'])
                    session['ingredienttype']= (response['ingredienttype'])
                    session['ingredientalchohol']= (response['ingredientalchohol'])
            else:
                cocktailname = "ERROR"
    return render_template('userpage.html')


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
                session['cocktailname'] = None
                session['thumbnail'] = None
                session['category']=None
                session['instructions']=None
                session['ingredients']=None
                session['measurements']=None
                session['ingredientname']=None
                session['ingredientdescription']=None
                session['ingredienttype']=None
                session['ingredientalchohol']=None
                session['favorite']=False
                return redirect('/userpage')
            else:
                return f"{response['message']}"
    return render_template('register.html')

@app.route('/favorites')
def favorites():
    session['cocktailname'] = None
    session['thumbnail'] = None
    session['category']=None
    session['instructions']=None
    session['ingredients']=None
    session['measurements']=None
    session['ingredientname']=None
    session['ingredientdescription']=None
    session['ingredienttype']=None
    session['ingredientalchohol']=None
    session['favorite']=False
    msg = messaging.Messaging()
    msg.send(
        'getfavorites',
        {
            'username' : session['username']
        }
    )
    response = msg.receive()
    return render_template('favorites.html',data=response)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')
