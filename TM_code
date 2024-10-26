# CAN ONLY RUN ON THE WEBPAGE

from pyscript.js_modules import teach, pose, ble_library, mqtt_library

async def run_model(URL2):
    s = teach.s  # or s = pose.s
    s.URL2 = URL2
    await s.init()

def get_predictions(num_classes):
    predictions = []
    for i in range (0,num_classes):
        divElement = document.getElementById('class' + str(i))
        if divElement:
            divValue = divElement.innerHTML
            predictions.append(divValue)
    return predictions

# mqtt
mqtt_broker = 'broker.hivemq.com'
port = 1883
topic_sub = '/djohnsen'       # this reads anything sent to ME35
client = mqtt_library.myClient
print('Connected to %s MQTT broker' % (mqtt_broker))
import asyncio
await run_model("https://teachablemachine.withgoogle.com/models/4knMXcILY3/") #Change to your model link
topic_pub = '/djohnsen'
while True:
    #if ble.connected:
    #    predictions = get_predictions(2)
    #    send(predictions)
    #await asyncio.sleep(2)
    predictions = get_predictions(4)
    values = [float(item.split(': ')[1]) for item in predictions]
    print(values)
    if values[0] >= 0.90:
        publish_command("/djohnsen", "loud")
    elif values[1] >= 0.90:
        publish_command("/djohnsen", "quiet")
    elif values[2] >= 0.90:
        publish_command("/djohnsen", "fast")
    elif values[3] >= 0.90:
        publish_command("/djohnsen", "slow")
    #else: send nothing
