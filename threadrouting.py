import asyncio
import random
import aiojobs
from didcomm_messaging import quickstart
from pprint import pprint
import logging
from router import MessageRouter


LOG = logging.getLogger('quickstart')
LOG.setLevel(logging.DEBUG)
# This demo is used to show some advanced routing tools
# run this, and paste the displayed DID into the DIDComm Demo (demo.didcomm.org)
# Send a basicmessage to interact

RELAY_DID = 'did:web:dev.cloudmediator.indiciotech.io'

async def profile_display(msg, contact_context, thread_context):
    print(f"Profile: {msg['body']['profile']['displayName']}\n---------------\n")

async def profile_request(msg, contact_context, thread_context):
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

async def run_await_process(msg):
    # running a multi message process.
    print("starting step process")
    async def ask(ask_message):
        await sendBasicMessage(msg['from'], ask_message)
        response_msg, response_contact_context, response_thread_context = await router.wait_for_message(msg['from'], "https://didcomm.org/basicmessage/2.0/message")
        #response_msg, response_context = await response_future
        return response_msg['body']['content']

    color_1 = await ask("What is your favorite color? (Await)")
    print(f"responded with color {color_1}")

    color_2 = await ask(f"And your second favorite color, other than {color_1}? (Await)")
    print(f"Two favorite Colors: {color_1} and {color_2}")

    await sendBasicMessage(msg['from'], f"Your two favorite colors are {color_1} and {color_2}. Thanks for responding. (Await)")


async def basicMessage(msg, contact_context, thread_context):
    message_content = msg['body']['content'].lower()

    if message_content == "await":
        await run_await_process(msg)  
    elif message_content == "colors": 
        contact_context.set('step', 'start')
        await sendBasicMessage(msg['from'], "What is your favorite color? (Colors)")
    elif message_content == "step":
        await start_new_step_process(msg, contact_context, thread_context)
    elif contact_context.get('step') == 'start':
        contact_context.set('color_1',  msg['body']['content'])
        contact_context.set('step', 'second_color')
        await sendBasicMessage(msg['from'], f"And your second favorite color, other than {contact_context.get('color_1')}? (Colors)")
    elif contact_context.get('step') == 'second_color':
        contact_context.set('color_2', msg['body']['content'])
        contact_context.set('step', 'complete')
        await sendBasicMessage(msg['from'], f"Your two favorite colors are {contact_context.get('color_1')} and {contact_context.get('color_2')}. Thanks for responding. (Colors)")
        contact_context.set('step', None)  # Reset the step for future interactions
    else:
        await sendBasicMessage(msg['from'], "Send 'colors' to start the state flow, 'await' to start the await flow, or 'step' to start the new step process.")

    print(f"Context after basicMessage: {contact_context}")

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

# New functions for the step process

async def start_new_step_process(msg, contact_context, thread_context):
    print("Starting new step process")
    router.engage_named_handler(msg['from'], "https://didcomm.org/basicmessage/2.0/message", "handle_new_color_1")
    await sendBasicMessage(msg['from'], "What is your favorite color? (Step)")

async def handle_new_color_1(msg, contact_context, thread_context):
    color_1 = msg['body']['content']
    contact_context.set('new_color_1', color_1)
    print(f"First favorite color (New process): {color_1}")
    router.engage_named_handler(msg['from'], "https://didcomm.org/basicmessage/2.0/message", "handle_new_color_2")
    await sendBasicMessage(msg['from'], f"And your second favorite color, other than {color_1}? (Step)")

async def handle_new_color_2(msg, contact_context, thread_context):
    color_2 = msg['body']['content']
    color_1 = contact_context.get('new_color_1')
    print(f"Two favorite Colors (New process): {color_1} and {color_2}")
    await sendBasicMessage(msg['from'], f"Your two favorite colors are {color_1} and {color_2}. Thanks for responding. (Step)")
    # We don't register a new handler here, so it will fall back to the default basicMessage handler



relayed_did = ""
DMP = None
router = None

async def main():
    global DMP
    global relayed_did
    global router
    scheduler = aiojobs.Scheduler()
    # setup message router

    router = MessageRouter(scheduler)
    
    # Register handlers
    # TODO: Add class based routers for whole protocols.
    router.add_route("https://didcomm.org/user-profile/1.0/profile", profile_display)
    router.add_route("https://didcomm.org/user-profile/1.0/request-profile", profile_request)
    router.add_route("https://didcomm.org/basicmessage/2.0/message", basicMessage)

    # Add other handlers to the handler_map
    router.add_named_handler(handle_new_color_1, "handle_new_color_1")
    router.add_named_handler(handle_new_color_2, "handle_new_color_2")

    did, secrets = quickstart.generate_did()

    # Setup the didcomm-messaging-python library object
    DMP = await quickstart.setup_default(did, secrets)

    # Connect to RELAY_DID as our inbound relay/mediator
    relayed_did = await quickstart.setup_relay(DMP, did, RELAY_DID, *secrets) or did
    print(f"our relayed did: \n{relayed_did}")

    print("Agent ready for messages...")

    # Have messages streamed to us via the relay/mediator's websocket
    try:
        await quickstart.websocket_loop(DMP, did, RELAY_DID, router.route_message)
    except asyncio.exceptions.CancelledError:
        print("Shutting down Agent.")
        await scheduler.close() 
    
    

asyncio.run(main())
