import pika
import time
import os
import psycopg2

# Sleep time for BE to connect
sleepTime = 20
print(' [*] Sleeping for ', sleepTime, ' seconds.')
time.sleep(sleepTime)

# Connect with Messaging
print(' [*] Connecting to server ...')
credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='messaging', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

# Connect with DB
print(' [*] Connecting to the database...')
postgres_user = os.environ['DB_USER']
postgres_password = os.environ['DB_PASS']

try:
    conn = psycopg2.connect(
        host='db',
        database='it490',
        user=postgres_user,
        password=postgres_password
    )

    cursor = conn.cursor()
    postgres_insert_query = """ INSERT INTO usersinfo (user_id, first_names, last_name, email, password, hash) VALUES (%s, %s, %s, %s, %s, %s)  """
    record_to_insert = (5, 'Kamal', 'Youssef',
                        'testemail2@gmail.com', 'password123', 'd3fmsdfsd3ksekfl')

    cursor.execute(postgres_insert_query, record_to_insert)

    conn.commit()
    count = cursor.rowcount
    print(count, "Record inserted successfully into usersinfo table")

except (Exception, psycopg2.Error) as error:
    if(connection):
        print("Failed to insert record into usersinfo table", error)

finally:
    # closing database connection.
    if(conn):
        cursor.close()
        conn.close()
        print("PostgreSQL connection is closed")


# Talking with Messaging
def callback(ch, method, properties, body):
    print(" [x] Received %s" % body)
    cmd = body.decode()

    if cmd == 'hey':
        print("hey there")
    elif cmd == 'hello':
        print("well hello there")
    else:
        print("sorry i did not understand ", body)

    print(" [x] Done")

    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
channel.start_consuming()
