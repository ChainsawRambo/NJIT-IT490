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
    if (connection):
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
        data = request['data']
        if action == 'GETHASH':
            response = get_hash(data)
        elif action == 'REGISTER':
            response = register_user(data)
        elif action == 'SCRAPE':
            response = scrape_data(data)
        elif action == 'favorite':
            response = favorite(data)
        elif action == 'getfavorites':
            response = getfavorites(data)
        else:
            response = {'success': False, 'message': "Unknown action"}
    logging.info(response)
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response)
    )

#Function Definitions

def scrape_data(data):
    search_by = data['dropdownvalue']
    if search_by == 'cocktail_name':
        response = search_cocktail_name(data)
    elif search_by == 'ingredient_name':
        response = search_ingredient_name(data)
    elif search_by == 'random':
        response = search_random(data)
    return response

def search_random(data):
    r = requests.get('https://www.thecocktaildb.com/api/json/v1/1/random.php')
    r = r.json()
    cocktail_name = r['drinks'][0]['strDrink']
    favorite = is_favorite(cocktail_name,data['username'])
    cocktail_image = r['drinks'][0]['strDrinkThumb']
    cocktail_ingredients = []
    cocktail_measurements = []
    for i in range(1, 16):
        add_cocktail_ingredients(cocktail_ingredients, i, r)
        add_cocktail_measurements(cocktail_measurements, i, r)
    cocktail_instructions = r['drinks'][0]['strInstructions']
    cocktail_category = r['drinks'][0]['strCategory']
    response = {
                    'success': True,
                    'search': 'random',
                    'cocktailname': cocktail_name,
                    'cocktailimage': cocktail_image,
                    'cocktailingredients': cocktail_ingredients,
                    'cocktailmeasurements': cocktail_measurements,
                    'cocktailinstructions': cocktail_instructions,
                    'cocktailcategory': cocktail_category,
                    'favorite': favorite
                }
    return response


def add_cocktail_measurements(cocktail_measurements, i, r):
    if r['drinks'][0]['strMeasure' + str(i)]:
        cocktail_measurements.append(r['drinks'][0]['strMeasure' + str(i)])


def add_cocktail_ingredients(cocktail_ingredients, i, r):
    if r['drinks'][0]['strIngredient' + str(i)]:
        cocktail_ingredients.append(r['drinks'][0]['strIngredient' + str(i)])


def search_ingredient_name(data):
    search_by_ingredient_name = {'i': data['searchfield']}
    r = requests.get('https://www.thecocktaildb.com/api/json/v1/1/search.php', params=search_by_ingredient_name)
    r = r.json()
    if r['ingredients']:
        ingredient_name = r['ingredients'][0]['strIngredient']
        ingredient_description = r['ingredients'][0]['strDescription']
        ingredient_type = r['ingredients'][0]['strType']
        ingredient_alchohol = r['ingredients'][0]['strAlcohol']
        response = {
                        'success': True,
                        'search': 'ingredient_name',
                        'ingredientname': ingredient_name,
                        'ingredientdescription': ingredient_description,
                        'ingredienttype': ingredient_type,
                        'ingredientalchohol': ingredient_alchohol
                    }
    else:
        response = {'success': False, 'message': "Invalid Ingredient Name"}
    return response


def search_cocktail_name(data):
    search_by_cocktail_name = {'s': data['searchfield']}
    r = requests.get('https://www.thecocktaildb.com/api/json/v1/1/search.php', params=search_by_cocktail_name)
    r = r.json()
    if r['drinks']:
        cocktail_name = r['drinks'][0]['strDrink']
        favorite = is_favorite(cocktail_name,data['username'])
        cocktail_image = r['drinks'][0]['strDrinkThumb']
        cocktail_ingredients = []
        cocktail_measurements = []
        for i in range(1, 16):
            add_cocktail_ingredients(cocktail_ingredients, i, r)
            add_cocktail_measurements(cocktail_measurements, i, r)
        cocktail_instructions = r['drinks'][0]['strInstructions']
        cocktail_category = r['drinks'][0]['strCategory']
        response = \
            {
                'success': True,
                'search': 'cocktail_name',
                'cocktailcategory': cocktail_category,
                'cocktailimage': cocktail_image,
                'cocktailingredients': cocktail_ingredients,
                'cocktailinstructions': cocktail_instructions,
                'cocktailmeasurements': cocktail_measurements,
                'cocktailname': cocktail_name,
                'favorite': favorite
            }
    else:
        response = {'success': False, 'message': "Invalid Cocktail Name"}
    return response


def register_user(data):
    firstname = data['firstname']
    lastname = data['lastname']
    email = data['email']
    username = data['username']
    hashed = data['hash']
    logging.info(f"REGISTER request for {email} received")
    cursor.execute('SELECT * FROM usersinfo WHERE email=%s or username=%s;', (email, username))
    if cursor.fetchone() != None:
        response = {'success': False, 'message': 'Username or email already exists'}
    else:
        cursor.execute('INSERT INTO usersinfo VALUES (%s, %s, %s, %s, %s);',
                       (username, firstname, lastname, email, hashed))
        conn.commit()
        response = {'success': True}
    return response

def favorite(data):
    username = data['username']
    favorite = data['fav']
    cursor.execute('SELECT * FROM usersfavorite WHERE userid=%s and cocktailname=%s;', (username,favorite))
    if cursor.fetchone() != None:
        cursor.execute('DELETE FROM usersfavorite WHERE userid=%s and cocktailname=%s;', (username, favorite))
        conn.commit()
        response = {'success': True, 'deleted': True, 'inserted':False, 'message': 'Deleted favorite'}
    else:
        cursor.execute('INSERT INTO usersfavorite VALUES (%s, %s);',
                       (username, favorite))
        conn.commit()
        response = {'success': True, 'deleted': False, 'inserted':True}
    return response

def is_favorite(cocktail,username):
    cursor.execute('SELECT * FROM usersfavorite WHERE userid=%s and cocktailname=%s;', (username,cocktail))
    if cursor.fetchone() != None:
        return True
    else:
        return False


def get_hash(data):
    username = data['username']
    logging.info(f"GETHASH request for {username} received")
    cursor.execute('SELECT hash FROM usersinfo WHERE username=%s;', (username,))
    row = cursor.fetchone()
    if row is None:
        response = {'success': False}
    else:
        response = {'success': True, 'hash': row[0]}
    return response

def getfavorites(data):
    username = data['username']
    #cursor.execute('SELECT * FROM usersfavorite inner join usersinfo on usersfavorite.userid=usersinfo.username WHERE usersinfo.username=%s;', (username,))
    cursor.execute('SELECT * FROM usersfavorite WHERE userid=%s;', (username,))
    '''
    row_headers=[x[0] for x in cursor.description]
    rv = cursor.fetchall()
    json_data=[]
    for result in rv:
        json_data.append(dict(zip(row_headers,result)))
    return json.dumps(json_data)
    '''
    rv = cursor.fetchall()
    result=[]
    for entry in rv:
        result.append(entry[1])

    response = {'success':True, 'cocktails':result}
    return response

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='request', auto_ack=True, on_message_callback=callback)
channel.start_consuming()
