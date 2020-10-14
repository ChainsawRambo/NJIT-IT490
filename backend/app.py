import pika
import time
import os
import psycopg2
import json
import logging
import requests
import urllib.parse

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

    #Old input code
    '''
    postgres_insert_query = """ INSERT INTO usersinfo (username, firstname, lastname, email, registration_date, hash) VALUES ( %s,%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)  """
    record_to_insert = ('ky98', 'Kamal', 'Youssef',
                        'testemail4324343@gmail.com', 'password123', 'd3fmsdf21342343sd3ksekfl')

    cursor.execute(postgres_insert_query, record_to_insert)

    conn.commit()
    count = cursor.rowcount
    print(count, "Record inserted successfully into usersinfo table")
    '''
except (Exception, psycopg2.Error) as error:
    if(connection):
        print("Failed to insert record into usersinfo table", error)

#Old code used to close DB connection
'''
finally:
    # closing database connection.
    if(conn):
        cursor.close()
        conn.close()
        print("PostgreSQL connection is closed")
'''
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
        # Pull hashed password
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
        #Insert user data from register
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
        else:
            response = {'success': False, 'message': "Unknown action"}
    logging.info(response)
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response)
    )

#Conenction with cocktail API
main_api= 'https://www.thecocktaildb.com/api/json/v1/1/search.php?'

#HARD CODED CHANGE LATER
cocktail='margarita'
url = main_api + urllib.parse.urlencode({'name': cocktail})

#JSON Output
json_data = requests.get(url).json()
print(json_data)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='request', auto_ack=True, on_message_callback=callback)
channel.start_consuming()
