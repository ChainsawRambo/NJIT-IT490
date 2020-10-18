import pika
import time
import os
import psycopg2
import json
import logging
import requests

# Sleep time for BE to connect
sleepTime = 20
print(' [*] Sleeping for ', sleepTime, ' seconds.')
time.sleep(sleepTime)

# Connect with Messaging
print(' [*] Connecting to server ...')
credentials = pika.PlainCredentials(os.environ['RABBITMQ_DEFAULT_USER'],
                                        os.environ['RABBITMQ_DEFAULT_PASS'])
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='messaging', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='request', durable=True)

# Connect with DB
print(' [*] Connecting to the database...')
postgres_user = os.environ['DB_USER']
postgres_password = os.environ['DB_PASS']

try:
    conn = psycopg2.connect(
        host='db',
        database='bartender',
        user=postgres_user,
        password=postgres_password
    )

except (Exception, psycopg2.Error) as error:
    if(connection):
        print("Failed to insert record into usersinfo table", error)

cursor = conn.cursor()

# Talking with Messaging
def callback(ch, method, properties, body):
    request = json.loads(body)
    if 'action' not in request:
        response = {
            'success': False,
            'message': "Request does not have action"
        }
    else:
        action = request['action']
        if action == 'GETHASH':
            data = request['data']
            username = data['username']
            logging.info(f"GETHASH request for {username} received")
            cursor.execute('SELECT hash FROM usersinfo WHERE username=%s;', (username,))
            row =  cursor.fetchone()
            if row == None:
                response = {'success': False}
            else:
                response = {'success': True, 'hash': row[0]}
        elif action == 'REGISTER':
            data = request['data']
            firstname = data['firstname']
            lastname = data ['lastname']
            email = data['email']
            username = data['username']
            hashed = data['hash']
            logging.info(f"REGISTER request for {email} received")
            cursor.execute('SELECT * FROM usersinfo WHERE email=%s or username=%s;', (email,username))
            if cursor.fetchone() != None:
                response = {'success': False, 'message': 'Username or email already exists'}
            else:
                cursor.execute('INSERT INTO usersinfo VALUES (%s, %s, %s, %s, %s);', (username, firstname, lastname, email, hashed))
                conn.commit()
                response = {'success': True}
        elif action == 'SCRAPE':
            data = request['data']
            searchby = data['dropdownvalue']
            if searchby == 'cocktail_name':
                searchbycocktailname = {'s':data['searchfield']}
                r = requests.get('https://www.thecocktaildb.com/api/json/v1/1/search.php', params=searchbycocktailname)
                r = r.json()
                if r['drinks']:
                    cocktailname=r['drinks'][0]['strDrink']
                    cocktailimage=r['drinks'][0]['strDrinkThumb']
                    cocktailingredients=[]
                    cocktailmeasurements=[]
                    for i in range(1,16):
                        if r['drinks'][0]['strIngredient' + str(i)]:
                            cocktailingredients.append(r['drinks'][0]['strIngredient' + str(i)])
                    for i in range(1,16):
                        if r['drinks'][0]['strMeasure' + str(i)]:
                            cocktailmeasurements.append(r['drinks'][0]['strMeasure' + str(i)])
                    cocktailinstructions=r['drinks'][0]['strInstructions']
                    cocktailcategory=r['drinks'][0]['strCategory']
                    response = {'success':True, 'search':'cocktail_name', 'cocktailname': cocktailname, 'cocktailimage': cocktailimage, 'cocktailingredients':cocktailingredients, 'cocktailmeasurements':cocktailmeasurements, 'cocktailinstructions':cocktailinstructions, 'cocktailcategory':cocktailcategory}
                else:
                    response = {'success': False, 'message': "Invalid Cocktail Name"}
            elif searchby == 'ingredient_name':
                searchbyingredientname = {'i':data['searchfield']}
                r = requests.get('https://www.thecocktaildb.com/api/json/v1/1/search.php', params=searchbyingredientname)
                r = r.json()
                if r['ingredients']:
                    ingredientname=r['ingredients'][0]['strIngredient']
                    ingredientdescription=r['ingredients'][0]['strDescription']
                    ingredienttype=r['ingredients'][0]['strType']
                    ingredientalchohol=r['ingredients'][0]['strAlcohol']
                    response = {'success':True, 'search':'ingredient_name', 'ingredientname': ingredientname, 'ingredientdescription' : ingredientdescription, 'ingredienttype': ingredienttype, 'ingredientalchohol': ingredientalchohol}
                else:
                    response = {'success': False, 'message': "Invalid Ingredient Name"}
            elif searchby == 'random':
                r = requests.get('https://www.thecocktaildb.com/api/json/v1/1/random.php')
                r=r.json()
                cocktailname=r['drinks'][0]['strDrink']
                cocktailimage=r['drinks'][0]['strDrinkThumb']
                cocktailingredients=[]
                cocktailmeasurements=[]
                for i in range(1,16):
                    if r['drinks'][0]['strIngredient' + str(i)]:
                        cocktailingredients.append(r['drinks'][0]['strIngredient' + str(i)])
                for i in range(1,16):
                    if r['drinks'][0]['strMeasure' + str(i)]:
                        cocktailmeasurements.append(r['drinks'][0]['strMeasure' + str(i)])
                cocktailinstructions=r['drinks'][0]['strInstructions']
                cocktailcategory=r['drinks'][0]['strCategory']
                response = {'success':True, 'search':'random', 'cocktailname': cocktailname, 'cocktailimage': cocktailimage, 'cocktailingredients':cocktailingredients, 'cocktailmeasurements':cocktailmeasurements, 'cocktailinstructions':cocktailinstructions, 'cocktailcategory':cocktailcategory}
        else:
            response = {'success': False, 'message': "Unknown action"}
    logging.info(response)
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response)
    )

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='request', auto_ack=True, on_message_callback=callback)
channel.start_consuming()
