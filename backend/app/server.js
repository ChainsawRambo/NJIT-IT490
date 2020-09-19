#!/usr/bin/env node

const https = require('https')

// Messaging configuration
const messaging_host = 'messaging';
const messaging_user = process.env.MSG_USER;
const messaging_pass = process.env.MSG_PASS;
const queue = 'requests';
const messaging_url = `amqp://${messaging_user}:${messaging_pass}@${messaging_host}`;
const amqp = require('amqplib/callback_api');

//Send talk with message
function send_response(channel, msg, response) {
    channel.sendToQueue(msg.properties.replyTo, Buffer.from(JSON.stringify(response)), {
        correlationId: msg.properties.correlationId
    });
    channel.ack(msg);
}