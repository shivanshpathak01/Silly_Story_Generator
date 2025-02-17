import conf,json,time,math,statistics
from boltiot import Sms,Bolt,Email
def compute(history_data,frame_size,factor):
    if len(history_data)<frame_size:
        return None
    if len(history_data)>frame_size:
        del history_data[0:len(history_data)-frame_size]
        Mn=statistics.mean(history_data)
        variance=0
        for data in history_data:
            variance+=math.pow((data-Mn),2)
        Zn=factor*math.sqrt(variance/frame_size)
        High_bound=history_data[frame_size-1]+Zn
        Low_bound=history_data[frame_size-1]-Zn
        return [High_bound,Low_bound]
history_data=[]
min=20.48
max=46.08
mybolt=Bolt(conf.API_KEY,conf.DEVICE_ID)
sms=Sms(conf.SID,conf.AUTH_TOKEN,conf.TO_NUMBER,conf.FROM_NUMBER)
mailer=Email(conf.MAILGUN_API_KEY,conf.SANDBOX_URL,conf.SENDER_EMAIL,conf.RECEPIENT_EMAIL)
while True:
    print("===========================================================================================================")
    print("Reading sensor value")
    response=mybolt.analogRead('A0')
    data=json.loads(response)
    if data['success']!=1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        continue
    try:
        sensor_value=int(data['value'])
    except Exception as e:
        print("There was an error while parsing the response:",e)
        continue
    value=sensor_value/10.24
    print("THE CURRENT TEMPERATURE:"+str(value))
    try:
        if sensor_value>max or sensor_value<min:
            mybolt.digitalWrite('0','HIGH')
            print("TEMPERATURE CROSSED THE LIMIT")
            response1=sms.send_sms("TEMPERATURE CROSSED THE LIMIT.THE CURRENT TEMPERATURE IS "+str(value))
            response2=mailer.send_email("ALERT!","TEMPERATURE CROSSED THE LIMIT.THE CURRENT TEMPERATURE IS "+str(value))
            print(response2)
            print("Status of SMS at Twilio is:"+str(response1.status))
            response_text=json.loads(response2.text)
            print("Response received from Mailgun is:"+str(response_text['message']))
            time.sleep(10)
            mybolt.digitalWrite('0','LOW')
    except Exception as e:
        print("Error occured:Below are the details")
        print(e)
        time.sleep(10)
        continue
    bound=compute(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
    print("-----------------------------------------------------------------------------------------------------------")
    if not bound:
        count=conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score.Need",count,"more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue
    try:
        if sensor_value> bound[0]  or sensor_value<bound[1]:
            mybolt.digitalWrite('0','HIGH')
            print("Alert! Someone opened the door")
            response1=sms.send_sms("ALERT! SOMEONE OPENED THE DOOR")
            print("Status of SMS at Twilio is:"+str(response1.status))
            response2=mailer.send_email("ALERT!","SOMEONE OPENED THE DOOR")
            response_text=json.loads(response2.text)
            print("This is the response for mail "+str(response_text['message']))
            time.sleep(10)
            mybolt.digitalWrite('0','LOW')
        history_data.append(sensor_value)
    except Exception as e:
        print("Error",e)
    time.sleep(10)