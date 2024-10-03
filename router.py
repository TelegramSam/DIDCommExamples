import functools
import asyncio

class MessageRouter:

    def __init__(self, _scheduler):
        self.routes = {}
        self.did_type = {} # used for one time routing
        self.scheduler = _scheduler
        self.contexts = {}  # New attribute to store context for each sending DID
    
    
    def add_route(self, msg_type, handler):
        if msg_type not in self.routes:
            self.routes[msg_type] = []
        self.routes[msg_type].append(handler)

    def add_message_route(self, msg_type):
        def decorator_route_message(func):
            self.add_route(msg_type, func)
            return func
        return decorator_route_message

    async def route_message(self, msg):
        msg_type = msg["type"]
        from_did = msg["from"]

        # Create or get context for the sending DID
        if from_did not in self.contexts:
            self.contexts[from_did] = {}
        context = self.contexts[from_did]

        # check instant routing
        fingerprint = f"{from_did}|{msg_type}"
        if fingerprint in self.did_type:
            print("Routing ONCE message")
            msg_future = self.did_type[fingerprint]
            msg_future.set_result((msg, context))  # Pass both msg and context
            del self.did_type[fingerprint] #remove the registered handler
            return #don't regular process the 'once' messages. This could be optional

        if msg_type in self.routes:
            for handler in self.routes[msg_type]:
                await self.scheduler.spawn(handler(msg, context))  # Pass both msg and context
        else:
            await self.unknown_handler(msg, context)  # Pass both msg and context

    async def unknown_handler(self, msg, context):
        print("Unknown Message: ", msg)
        print("Context: ", context)

    def wait_for_message(self, from_did, msg_type):
        # Create a new Future object.
        message_future = asyncio.get_running_loop().create_future()

        fingerprint = f"{from_did}|{msg_type}"
        self.did_type[fingerprint] = message_future

        return message_future # this can be awaited.
