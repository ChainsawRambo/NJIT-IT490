from flask import Flask, render_template, request, session
#from werkzeug.security import check_password_hash, generate_password_hash, gen_salt
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
        '''
        response = msg.receive()
        if response['success'] != True:
            return "Login failed."
        if check_password_hash(response['hash'], password):
            session['email'] = email
            return redirect('/')
        else:
            return "Login failed."
        '''
    return render_template('login.html')

@app.route('/register')
def registerpage():
    return render_template('register.html')
