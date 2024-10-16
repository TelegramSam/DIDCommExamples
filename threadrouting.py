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

#@router.add_message_route("https://didcomm.org/user-profile/1.0/profile")
async def profile_display(msg, context):
    print(f"Profile: {msg['body']['profile']['displayName']}\n---------------\n")
    print(f"Context: {context}") 

async def profile_request(msg, context):
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
    print(f"Context: {context}")
    await quickstart.send_http_message(DMP, relayed_did, response, target=msg['from'])

async def run_step_process(msg):
    # running a multi message process.
    print("starting step process")
    async def ask(ask_message):
        await sendBasicMessage(msg['from'], ask_message)
        response_msg, response_context = await router.wait_for_message(msg['from'], "https://didcomm.org/basicmessage/2.0/message")
        #response_msg, response_context = await response_future
        return response_msg['body']['content']

    color_1 = await ask("What is your favorite color?")
    print(f"responded with color {color_1}")

    color_2 = await ask(f"And your second favorite color, other than {color_1}?")
    print(f"Two favorite Colors: {color_1} and {color_2}")

    await sendBasicMessage(msg['from'], f"Your two favorite colors are {color_1} and {color_2}. Thanks for responding.")

# New functions for the step process

async def start_new_step_process(msg, context):
    print("Starting new step process")
    await sendBasicMessage(msg['from'], "What is your favorite color? (New step process)")
    router.register_handler(msg['from'], "https://didcomm.org/basicmessage/2.0/message", handle_new_color_1)

async def handle_new_color_1(msg, context):
    color_1 = msg['body']['content']
    context['new_color_1'] = color_1
    print(f"First favorite color (New process): {color_1}")
    await sendBasicMessage(msg['from'], f"And your second favorite color, other than {color_1}? (New step process)")
    router.register_handler(msg['from'], "https://didcomm.org/basicmessage/2.0/message", handle_new_color_2)

async def handle_new_color_2(msg, context):
    color_2 = msg['body']['content']
    color_1 = context['new_color_1']
    print(f"Two favorite Colors (New process): {color_1} and {color_2}")
    await sendBasicMessage(msg['from'], f"Your two favorite colors are {color_1} and {color_2}. Thanks for responding. (New step process)")
    # We don't register a new handler here, so it will fall back to the default basicMessage handler


async def basicMessage(msg, context):
    message_content = msg['body']['content'].lower()

    if 'step' not in context:
        context['step'] = None

    if message_content == "await":
        await run_step_process(msg)  
    elif message_content == "colors": 
        context['step'] = 'start'
        await sendBasicMessage(msg['from'], "What is your favorite color?")
    elif message_content == "step":
        await start_new_step_process(msg, context)
    elif context['step'] == 'start':
        context['color_1'] = msg['body']['content']
        context['step'] = 'second_color'
        await sendBasicMessage(msg['from'], f"And your second favorite color, other than {context['color_1']}?")
    elif context['step'] == 'second_color':
        context['color_2'] = msg['body']['content']
        context['step'] = 'complete'
        await sendBasicMessage(msg['from'], f"Your two favorite colors are {context['color_1']} and {context['color_2']}. Thanks for responding.")
        print(f"Two favorite Colors: {context['color_1']} and {context['color_2']}")
        context['step'] = None  # Reset the step for future interactions
    else:
        await sendBasicMessage(msg['from'], "Send 'colors' to start the state flow, 'await' to start the await flow, or 'step' to start the new step process.")

    print(f"Context after basicMessage: {context}")

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
    scheduler = aiojobs.Scheduler()
    # setup message router

    router = MessageRouter(scheduler)
    
    # Register handlers
    router.add_route("https://didcomm.org/user-profile/1.0/profile", profile_display)
    router.add_route("https://didcomm.org/user-profile/1.0/request-profile", profile_request)
    router.add_route("https://didcomm.org/basicmessage/2.0/message", basicMessage)

    # Add other handlers to the handler_map
    router.handler_map.update({
        "handle_new_color_1": handle_new_color_1,
        "handle_new_color_2": handle_new_color_2,
        "start_new_step_process": start_new_step_process,
        "run_step_process": run_step_process,
    })

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
