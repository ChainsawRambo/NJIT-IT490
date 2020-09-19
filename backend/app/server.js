#!/usr/bin/env node

const https = require('https')

// Messaging configuration
const messaging_host = 'messaging';
const messaging_user = process.env.MSG_USER;
const messaging_pass = process.env.MSG_PASS;
const queue = 'requests';
const messaging_url = `amqp://${messaging_user}:${messaging_pass}@${messaging_host}`;
const amqp = require('amqplib/callback_api');

// Function to send response
function send_response(channel, msg, response) {
    channel.sendToQueue(msg.properties.replyTo, Buffer.from(JSON.stringify(response)), {
        correlationId: msg.properties.correlationId
    });
    channel.ack(msg);
}

// Communications
amqp.connect(messaging_url, function(error0, connection) {
    if (error0) {
        throw error0;
    }
    connection.createChannel(function (error1, channel) {
        if (error1) {
            throw error1;
        }
        channel.assertQueue(queue, {
            durable: false
        });
        channel.prefetch(1);
        console.log('Listening for requests...');
        channel.consume(queue, function reply(msg) {
            console.log(`Received: ${msg.content}`);
            var received_json = JSON.parse(msg.content);
            var action = received_json['action'];
            switch (action) {
                //Communicating with message
                case 'ECHO':
                    data = received_json['data'];
                    console.log(`Echoing ${data}`);
                    send_response(channel, msg, {'status': 'OK', 'data': data});
                    break;

                // Error messages
                default:
                    console.log('Unknown action');
                    send_response(channel, msg, {'status': 'ERROR', 'message': 'Unknown action'});
                    break;
            }
        });
    });
});