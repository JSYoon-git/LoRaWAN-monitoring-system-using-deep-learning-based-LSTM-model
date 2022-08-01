from twilio.rest import Client 


account_sid = 'xxxxxxxxxxxxxxxxxx' 
auth_token = 'xxxxxxxxxxxxxxxxxx' 
client = Client(account_sid, auth_token) 


def send_SMS(pred):
    if pred >= 36:
        state = 'bad'
    elif pred >= 15 and pred < 36:
        state = 'normal'
    else:
        state = 'good'
    body = "After 1 hour, PM2.5 will be changed %d. It is normal %s."%(pred, state)
    message = client.messages.create( 
                                     to="개인정보", 
                                     from_="개인정보", 
                                     body="body") 

