#Imports
import pika
import time

print("TEST Back End Is Running Now")

#Sleep to allow other services to start first
time.sleep(20)

#Back End Code
print("Back End Is Running Now")
credentials = pika.PlainCredentials('guest','guest')
#connection = pika.BlockingConnection(
#	pika.ConnectionParameters(
#           host='messaging',
#           credentials=credentials
#       )
#)