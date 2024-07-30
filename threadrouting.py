import asyncio
import random
from didcomm_messaging import quickstart
from pprint import pprint

# This demo is used to show some advanced routing tools
# run this, and paste the displayed DID into the DIDComm Demo (demo.didcomm.org)
# Send a basicmessage containing 'count' to start the interesting process

# Note: currently not working correctly, likely as a result of screwing up something with Futures.

RELAY_DID = 'did:web:dev.cloudmediator.indiciotech.io'

async def process_msg(msg):
    print("Received Message: ", msg["type"], msg["body"])

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
        if msg_type in self.routes:
            for handler in self.routes[msg_type]:
                await handler(msg)
        else:
            await self.unknown_handler(msg)

        # check instant routing
        fingerprint = f"{msg['from']}|{msg['type']}"
        print(f".. checking for fingerprint {fingerprint}")
        if fingerprint in self.did_type:
            print(f".. Found Instant Future!")
            msg_future = self.did_type[fingerprint]
            msg_future.set_result(msg)


    async def unknown_handler(self, msg):
        print("Unknown Message: ", msg)

    def wait_for_message(self, from_did, msg_type):
        # Create a new Future object.
        message_future = asyncio.get_running_loop().create_future()

        fingerprint = f"{from_did}|{msg_type}"

        print(f".. waiting for fingerprint {fingerprint}")

        self.did_type[fingerprint] = message_future
        pprint(self.did_type)

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

    await ask("Send a basicmessage with color")
    msg_1_future = router.wait_for_message(msg['from'], "https://didcomm.org/basicmessage/2.0/message")
    print(f"future created {msg_1_future}")
    msg_1 = await msg_1_future
    print(f"got answer back {msg_1}")

    print(f"responded with color {msg_1['body']['content']}")



async def basicMessage(msg):
    #if message is anything other than 'count', then just display.
    message_content = msg['body']['content']
    if message_content == "count":
        await run_step_process(msg)
    else:
        print(f"BasicMessage: {message_content}")

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

async def main():
    global DMP
    global relayed_did
    global router
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
    
    

asyncio.run(main())