import paho.mqtt.client as mqtt
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import random
import ssl

class Participant:
    def __init__(self, network: str, encrypt:bool=False):
        self.network = self.formatNetwork(network) #the name of the grid network
        self.broker = "test.mosquitto.org"
        self.client_id = ""
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2) #,client_id=self.client_id, clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport="tcp"
        self.client.on_connect = self.on_connect
        self.client.on_connect_fail = self.on_connect_fail
        #self.client.on_log = self.on_log
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.timezone = ZoneInfo("America/New_York")
        self.port = self.getPort(encrypt) # true = encrypted, false = unencrypted
        self.path = 'demandResponseController/'
        if encrypt:
            self.client.tls_set(ca_certs=self.path +"keys/mosquitto.org.crt", certfile=self.path +"keys/client.crt",keyfile=self.path +"keys/client.key", tls_version=ssl.PROTOCOL_TLSv1_2)
        self.client.username_pw_set(None, password=None)
        self.message = {'message':''}
        #self.loop = asyncio.get_event_loop()
    
    def getPort(self,encrypt:bool=False)->int:
        '''
        if true, port 8884 is used (encrypted, client certificate required)
        else, port 1883 is used (unencrypted, unauthenticated)
        '''
        if encrypt:
            myPort = 8884
        else:
            myPort = 1883
        return myPort

    def formatNetwork(self,n:str)->str:
        n = n.replace(' ','')
        print(f'Network: {n}')
        return n
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, reason_code, properties)->None:
        if reason_code.is_failure:
            print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            print("Connected to ", client._host, "port: ", client._port)
            print("Flags: ", flags, "returned code: ", reason_code)
            client.subscribe("OpenDemandResponse/Event/"+self.network, qos=0)
    
    def on_connect_fail(self, client, userdata)->None:
        print("Failed to connect")

    def on_log(self, client, userdata, level, buf)->None:
        print(level)
        print(buf)

    # The callback for when a message is published.
    def on_publish(self, client, userdata, mid, reason_code, properties)->None:
        pass
    
    # The callback for when a message is received.
    def on_message(self, client, userdata, msg)->None:
        message = str(msg.payload.decode("utf-8"))
        if msg.topic == "OpenDemandResponse/Event/"+self.network:
            event, event_type, start_time,timestamp = message.split("#")
            self.data = {'event':event,'type':event_type,'start_time':start_time,'msg_timestamp':timestamp}
            print('********* RECIEVING *******************')
            print("{} {} event, starting at {}".format(event, event_type, start_time))
            print('***************************************')
            self.message = message

    async def async_on_message(self, message):
        async with lock:
            mqtt_message['message']=message

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties)->None:
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry
        if reason_code_list[0].is_failure:
            print(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties)->None:
        # Be careful, the reason_code_list is only present in MQTTv5.
        # In MQTTv3 it will always be empty
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
        else:
            print(f"Broker replied with failure: {reason_code_list[0]}")
        client.disconnect()

    def start(self,freq:int=60)->None:
        #self.client.connect(self.broker, port=self.port, keepalive=60)
        self.client.connect_async(self.broker, port=self.port, keepalive=60)
        self.client.loop_start()

        # while True:
        #     timestamp = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")
        #     self.client.publish("OpenDemandResponse/Participant/AlexN", payload="#test!!", qos=0, retain=False)
        #     await asyncio.sleep(freq)

    def publish(self, data)->None:
        timestamp = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")

        d = []
        for k, v in data.items():
            d.append(str(v))
        d.append(timestamp)
        print('%%%%%% PUBLISHING %%%%%%')
        print(d)
        print('%%%%%%%%%%%%%%%%%%%')
        self.client.publish("OpenDemandResponse/Participant/AlexN", payload="#".join(d), qos=0, retain=False)
        self.client.publish("OpenDemandResponse/participants", payload="AlexN", qos=0, retain=False)

        #     timestamp = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")
        #     self.client.publish("OpenDemandResponse/Participant/AlexN", payload="#test!!", qos=0, retain=False)
        #     await asyncio.sleep(freq)

    
    def stop_tracking(self)->None:
        self.client.loop_stop()
        self.client.disconnect()

class Aggregator:
    def __init__(self):
        self.broker = "test.mosquitto.org"
        self.client_id = ""
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=self.client_id, clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport="tcp")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.timezone = ZoneInfo("America/New_York")
        self.port = getPort(False) # true = encrypted, false = unencrypted
        self.client.username_pw_set(None, password=None)
        if encrypt:
            self.client.tls_set(ca_certs="keys/mosquitto.org.crt", certfile="keys/client.crt",keyfile="keys/client.key", tls_version=ssl.PROTOCOL_TLSv1_2) #needed for ports 8883 and 8884
        self.records = {}
    
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc)->None:
        print("Connected to ", client._host, "port: ", client._port)
        print("Flags: ", flags, "returned code: ", rc)
        client.subscribe("OpenDemandResponse/Participant/AlexN", qos=0)
        
    # The callback for when a message is published.
    def on_publish(self, client, userdata, mid)->None:
        pass
    
    # The callback for when a message is received.
    def on_message(self, client, userdata, msg)->None:
        message = str(msg.payload.decode("utf-8"))
        #print(message)
        if msg.topic == "OpenDemandResponse/Participant/AlexN":
            print('')
            try:
                battery, ac_out, ac_in, dc_out, dc_in, r1, pv, rpi, load, timestamp = message.split("#")
                print("Data at {}".format(timestamp))
                print("Battery: {}% \nload: {}\nAC Out: {}W, AC In: {}W, DC Out: {}W, DC In: {}W\nRelay State: {}\nPV: {}W\nRaspberry Pi: {}W".format(battery, load, ac_out, ac_in,dc_out, dc_in,r1,pv, rpi))
            except:
                print('data mismatch, dumping message')
                print(message)


    
    # def on_connect_fail(self, client, userdata):
    #     print("Failed to connect")

    # def on_log(self, client, userdata, level, buf):
    #     print(level)
    #     print(buf)

    def getPort(self, encrypt:bool=False)-> int:
        '''
        if true, port 8884 is used (encrypted, client certificate required)
        else, port 1883 is used (unencrypted, unauthenticated)
        '''
        if encrypt:
            myPort = 8884
        else:
            myPort = 1883
        return myPort

    # returns some key
    def auth(self)->str:
        return gfdgsdfhsdfsjdf

    async def run(self, freq:int=60)->None:
        self.client.connect(self.broker, port=self.port, keepalive=60)
        self.client.loop_start()
        authUpdate = False
        while True:
            event = eventNames[random.randint(0,len(eventNames)-1)]
            event_type = eventTypes[random.randint(0,len(eventTypes)-1)]
            start_time = eventTimes[random.randint(0,len(eventTimes)-1)]

            # update key when first connected
            if authUpdate:
                a = self.auth()
                self.client.publish("OpenDemandResponse/Auth", payload=a, qos=0, retain=False)
                authUpdate = False
            update = True
            if update:
                timestamp = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
                self.client.publish("OpenDemandResponse/Event/BoroughHall", payload="#".join([event, event_type, str(start_time), timestamp]), qos=0, retain=False)

            #time.sleep(freq)
            await asyncio.sleep(freq)

    
    def stop_tracking(self)->None:
        self.client.loop_stop()
        self.client.disconnect()
