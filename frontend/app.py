from flask import Flask, render_template
import pika

app = Flask(__name__)


@app.route('/')
def loginpage():
    return render_template('login.html')

@app.route('/register')
def registerpage():
    return render_template('register.html')


@app.route('/add-job/<cmd>')
def add(cmd):
    credentials = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='messaging', credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=cmd,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    connection.close()
    return " [x] Sent: %s" % cmd


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
