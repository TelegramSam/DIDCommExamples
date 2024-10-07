import functools
import asyncio

class NamedFunctionHandler:
    """
    Handles the registration and retrieval of named functions for specific DID and message type combinations.
    """

    def __init__(self):
        self.registered_handlers = {}

    def register(self, from_did, msg_type, handler_name):
        """
        Register a handler name for a specific DID and message type combination.
        """
        key = f"{from_did}|{msg_type}"
        self.registered_handlers[key] = handler_name

    def get_handler(self, from_did, msg_type):
        """
        Retrieve the handler name for a specific DID and message type combination.
        """
        key = f"{from_did}|{msg_type}"
        return self.registered_handlers.get(key)

    def remove_handler(self, from_did, msg_type):
        """
        Remove the handler for a specific DID and message type combination.
        """
        key = f"{from_did}|{msg_type}"
        if key in self.registered_handlers:
            del self.registered_handlers[key]

class MessageRouter:
    """
    Routes messages based on their type and handles the execution of appropriate handlers.
    """

    def __init__(self, _scheduler):
        self.routes = {}
        self.did_type = {}  # used for one time routing
        self.scheduler = _scheduler
        self.contexts = {}  # Store context for each sending DID
        self.named_function_handler = NamedFunctionHandler()
        self.handler_map = {}  # Store mapping of handler names to actual functions
    
    def add_route(self, msg_type, handler):
        """
        Add a route for a specific message type.
        """
        if msg_type not in self.routes:
            self.routes[msg_type] = []
        handler_name = handler.__name__
        self.routes[msg_type].append(handler_name)
        self.handler_map[handler_name] = handler

    def add_message_route(self, msg_type):
        """
        Decorator for adding a message route.
        """
        def decorator_route_message(func):
            self.add_route(msg_type, func)
            return func
        return decorator_route_message

    def register_handler(self, from_did, msg_type, handler):
        """
        Register a handler for a specific DID and message type combination.
        """
        handler_name = handler.__name__
        self.named_function_handler.register(from_did, msg_type, handler_name)
        self.handler_map[handler_name] = handler

    async def route_message(self, msg):
        """
        Route a message to the appropriate handler(s).
        """
        msg_type = msg["type"]
        from_did = msg["from"]

        # Create or get context for the sending DID
        if from_did not in self.contexts:
            self.contexts[from_did] = {}
        context = self.contexts[from_did]

        # Check for registered handler
        handler_name = self.named_function_handler.get_handler(from_did, msg_type)
        if handler_name:
            self.named_function_handler.remove_handler(from_did, msg_type)
            handler = self.handler_map.get(handler_name)
            if handler:
                await self.scheduler.spawn(handler(msg, context))
            return

        # check instant routing
        fingerprint = f"{from_did}|{msg_type}"
        if fingerprint in self.did_type:
            print("Routing ONCE message")
            msg_future = self.did_type[fingerprint]
            msg_future.set_result((msg, context))  # Pass both msg and context
            del self.did_type[fingerprint]  # remove the registered handler
            return  # don't regular process the 'once' messages. This could be optional

        if msg_type in self.routes:
            for handler_name in self.routes[msg_type]:
                handler = self.handler_map.get(handler_name)
                if handler:
                    await self.scheduler.spawn(handler(msg, context))
        else:
            await self.unknown_handler(msg, context)

    async def unknown_handler(self, msg, context):
        """
        Handle unknown message types.
        """
        print("Unknown Message: ", msg)
        print("Context: ", context)

    def wait_for_message(self, from_did, msg_type):
        """
        Wait for a specific message from a DID.
        """
        # Create a new Future object.
        message_future = asyncio.get_running_loop().create_future()

        fingerprint = f"{from_did}|{msg_type}"
        self.did_type[fingerprint] = message_future

        return message_future  # this can be awaited.