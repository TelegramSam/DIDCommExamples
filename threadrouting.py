import asyncio
import random
import aiojobs
from didcomm_messaging import quickstart
from pprint import pprint
import logging


LOG = logging.getLogger('quickstart')
LOG.setLevel(logging.DEBUG)
# This demo is used to show some advanced routing tools
# run this, and paste the displayed DID into the DIDComm Demo (demo.didcomm.org)
# Send a basicmessage to interact

RELAY_DID = 'did:web:dev.cloudmediator.indiciotech.io'

class MessageRouter:

    def __init__(self):
        self.routes = {}
        self.did_type = {} # used for one time routing

    def add_route(self, msg_type, handler):
        if msg_type not in self.routes:
            self.routes[msg_type] = []
        self.routes[msg_type].append(handler)

    async def route_message(self, msg):
        msg_type = msg["type"]

        # check instant routing
        fingerprint = f"{msg['from']}|{msg['type']}"
        if fingerprint in self.did_type:
            print("Routing ONCE message")
            msg_future = self.did_type[fingerprint]
            msg_future.set_result(msg)
            del self.did_type[fingerprint] #remove the registered handler
            return #don't regular process the 'once' messages. This could be optional


        if msg_type in self.routes:
            for handler in self.routes[msg_type]:
                await scheduler.spawn(handler(msg)) # ends up in the background
        else:
            await self.unknown_handler(msg)




    async def unknown_handler(self, msg):
        print("Unknown Message: ", msg)

    def wait_for_message(self, from_did, msg_type):
        # Create a new Future object.
        message_future = asyncio.get_running_loop().create_future()

        fingerprint = f"{from_did}|{msg_type}"
        self.did_type[fingerprint] = message_future

        return message_future # this can be awaited.



async def profile_display(msg):
    print(f"Profile: {msg['body']['profile']['displayName']}\n---------------\n")

async def profile_request(msg):
    response = {
        "type": "https://didcomm.org/user-profile/1.0/profile",
        # "id": str(uuid.uuid4()),
        "body": {
            "profile": {
            "displayName": f"RoutingExample-{random.randrange(1, 10)}"
            }
        },
        "from": relayed_did,
        "lang": "en",
        "to": [msg['from']],
        "thid": msg['id']
    }
    print(f"Requested Profile. Responding. \n {response}")
    await quickstart.send_http_message(DMP, relayed_did, response, target=msg['from'])

async def run_step_process(msg):
    # running a multi message process.
    print("starting step process")
    async def ask(ask_message):
        await sendBasicMessage(msg['from'], ask_message)
        response_msg = await router.wait_for_message(msg['from'], "https://didcomm.org/basicmessage/2.0/message")
        return response_msg['body']['content']

    color_1 = await ask("What is your favorite color?")

    print(f"responded with color {color_1}")

    color_2 = await ask(f"And your second favorite color, other than {color_1}?")

    print(f"Two favorite Colors: {color_1} and {color_2}")
    await sendBasicMessage(msg['from'], f"Your two favorite colors are {color_1} and {color_2}. Thanks for responding.")


async def basicMessage(msg):
    #if message is anything other than 'colors', then prompt.
    message_content = msg['body']['content']
    if message_content == "colors":
        await run_step_process(msg)
    else:
        await sendBasicMessage(msg['from'], f"Send 'colors' to start the flow.")

async def sendBasicMessage(to_did, msg):     # Send a message to target_did from the user
    message = {
        "type": "https://didcomm.org/basicmessage/2.0/message",
        # "id": str(uuid.uuid4()),
        "body": {"content": msg},
        "from": relayed_did,
        "lang": "en",
        "to": [to_did],
    }
    await quickstart.send_http_message(DMP, relayed_did, message, target=to_did)

relayed_did = ""
DMP = None
router = None
scheduler = None

async def main():
    global DMP
    global relayed_did
    global router
    global scheduler
    scheduler = aiojobs.Scheduler()
    did, secrets = quickstart.generate_did()

    # Setup the didcomm-messaging-python library object
    DMP = await quickstart.setup_default(did, secrets)

    # Connect to RELAY_DID as our inbound relay/mediator
    relayed_did = await quickstart.setup_relay(DMP, did, RELAY_DID, *secrets) or did
    print(f"our relayed did: \n{relayed_did}")

    # setup message router
    router = MessageRouter()
    router.add_route("https://didcomm.org/user-profile/1.0/profile", profile_display)
    router.add_route("https://didcomm.org/user-profile/1.0/request-profile", profile_request)
    router.add_route("https://didcomm.org/basicmessage/2.0/message", basicMessage)

    print("Agent ready for messages...")

    # Have messages streamed to us via the relay/mediator's websocket
    try:
        await quickstart.websocket_loop(DMP, did, RELAY_DID, router.route_message)
    except asyncio.exceptions.CancelledError:
        print("Shutting down Agent.")
        await scheduler.close() 
    
    

asyncio.run(main())