import os, sys
from flask import Flask, request
import json
import requests
from airtable import Airtable

#CUSTOM
from utils import KNOWLEDGE_NEURAL , KNOWLEDGE_COLOR, base_key, table_name

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
	# Webhook verification
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200


@app.route('/', methods=['POST'])   
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
      # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":   # make sure this is a page subscription

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):     # someone sent us a message
                    received_message(messaging_event)
                    # received_authentication(messaging_event)

                elif messaging_event.get("optin"):     # optin confirmation
                    received_optin(messaging_event)

                elif messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    received_postback(messaging_event)

                else:    # uknown messaging_event
                    pass

    return "ok", 200



def received_message(event):

    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
    
    # could receive text or attachment but not both
    if "text" in event["message"]:
        message_text = event["message"]["text"]
        print(message_text)

        if message_text == 'Color Images':
            send_text_message(sender_id,"Upload black and white image")
        elif message_text == 'Neural Image Style':
            send_text_message(sender_id,"Upload Two images simultaneausly")
        elif message_text == 'Color Extractor':
            one_time_notify(sender_id)
            

    elif "attachments" in event["message"]:
        attachments = event["message"]["attachments"]

        if len(attachments) == 1:
            image_url = event["message"]["attachments"][0]["payload"]["url"]
            send_text_message(sender_id,"Processing...")
            send_colored_image(sender_id,image_url)
            

        if len(attachments) == 2:
            content_image_url = event["message"]["attachments"][0]["payload"]["url"]
            style_image_url= event["message"]["attachments"][1]["payload"]["url"]
            
            send_text_message(sender_id,"Processing...")
            send_neural_style_image(sender_id,content_image_url,style_image_url)





airtable = Airtable(base_key, table_name,api_key = os.environ['AIRTABLE_API_KEY'])
def send_colored_image(recipient_id,image_url):
    
    r = requests.post(
        "https://api.deepai.org/api/colorizer",
        data={
            'image': image_url,
        },
        headers={'api-key': 'DEEP-AI_API_KEY'}
    )

    colored_image = r.json()['output_url']

    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"image",
                "payload":{
                    "url": colored_image,
                    
                }
            }
        }
    })

    call_send_api(message_data) 
    #attachment_id = result.json()['attachment_id']


    def create_record():
        url = colored_image
        airtable.insert({'saved_url': url})
    create_record()
    show_services(recipient_id)


    
def send_neural_style_image(recipient_id,content_image_url,style_image_url):
    r = requests.post(
        "https://api.deepai.org/api/neural-style",
        data={
            'style': content_image_url,
            'content': style_image_url
        },
        headers={'api-key': 'DEEP-AI_API_KEY'} #REPLACE WITH ACTUAL API KEY
    )
    neural_image = r.json()['output_url']

    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"image",
                "payload":{
                    "url": neural_image
                }
            }
        }
    })

    
    call_send_api(message_data)
    def create_record():
        url = neural_image
        airtable.insert({'saved_url': url})
    create_record()
    show_services(recipient_id)



def received_postback(event):

    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

    # The payload param is a developer-defined field which is set in a postback
    # button for Structured Messages
    payload = event["postback"]["payload"]

    if payload == 'Get Started':
        show_services(sender_id)
    elif payload == 'Credits Left':
        show_credits_left(sender_id)
    elif payload == 'Knowledge Hunt':
        show_knowledge_hunt(sender_id)
    elif payload == "knowledge_neural":
        knowledge_neural(sender_id)
    elif payload == "knowledge_color":
        knowledge_color(sender_id)
    elif payload == "My Assets":
        send_text_message(sender_id,"Your recent saved asset is below")
        show_saved_assets(sender_id)
    else:
        # Notify sender that postback was successful
        send_text_message(sender_id,"Postback successfull")


    
def show_saved_assets(recipient_id):
    result = airtable.get_all(fields=['saved_url'])
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "image",
                "payload": {
                    "url": result[0]['fields']['saved_url']
                }
            }
        }
    })
    call_send_api(message_data)
    show_services(recipient_id)
        
    
def show_knowledge_hunt(recipient_id):
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "attachment":{
                "type":"template",
                "payload":{
                    "template_type":"generic",
                    "elements":[
                        {
                            "title":"Neural Image Style",
                            "image_url":"https://tensorflow.org/tutorials/generative/images/stylized-image.png",
                            "buttons":[
                                {
                                    "type":"postback",
                                    "title":"Neural Image",
                                    "payload": "knowledge_neural"
                                }
                            ]
                        },
                        {
                            "title":"Coloring Images",
                            "image_url":"https://cdn.guidingtech.com/imager/assets/2019/10/240182/black-and-white-to-color-online-fi_935adec67b324b146ff212ec4c69054f.jpg?1569946301",
                            "buttons":[
                                {
                                    "type":"postback",
                                    "title":"Color Images",
                                    "payload": "knowledge_color"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    })

    call_send_api(message_data)

def knowledge_neural(recipient_id):
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": KNOWLEDGE_NEURAL
        }
    })

    call_send_api(message_data)
    show_services(recipient_id)
    
def knowledge_color(recipient_id):
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": KNOWLEDGE_COLOR
        }
    })

    call_send_api(message_data)
    show_services(recipient_id)
    
def received_optin(event):
    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]

    payload = event["optin"]["payload"] 
    one_time_notif_token = event["optin"]["one_time_notif_token"]
    print(payload)
    print(one_time_notif_token)
    if payload == 'Notify Me':
        reply_notify(sender_id,one_time_notif_token)

def reply_notify(recipient_id,one_time_notif_token):
    message_data = json.dumps({
        "recipient":{
            "one_time_notify_token": one_time_notif_token
        },
        "message":{
            "text": "You will be notified"
        }
    })
    call_send_api(message_data)


def show_credits_left(recipient_id):
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": "You have 3 credits left"
        }
    })

    call_send_api(message_data)
    show_services(recipient_id)
    
def send_text_message(recipient_id,message_text):
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })

    call_send_api(message_data)

def show_services(recipient_id):
    message_data = json.dumps({
        "recipient":{
            "id":recipient_id
        },
        "messaging_type": "RESPONSE",
        "message":{
            "text": "Choose a service",
            "quick_replies":[
                {
                    "content_type":"text",
                    "title":"Color Images",
                    "payload":"postback",
                },
                {
                    "content_type":"text",
                    "title":"Color Extractor",
                    "payload":"postback",
                },
                {
                    "content_type":"text",
                    "title":"Neural Image Style",
                    "payload":"postback",
                }
            ]
        }
    })
    call_send_api(message_data)


def one_time_notify(recipient_id):
    message_data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "attachment":{
                "type":"template",
                "payload":{
                    "template_type":"one_time_notif_req",
                    "title":"When Color Extractor service will be available",
                    "payload":"Notify Me"
                }
                
            }
        }
    })
    call_send_api(message_data)
    

#MAIN FUNCTION CALL
def call_send_api(message_data):

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }

    
    r = requests.post("https://graph.facebook.com/v7.0/me/messages", params=params, headers=headers, data=message_data)
    


if __name__ == "__main__":
	app.run(debug = True, port = 80)







