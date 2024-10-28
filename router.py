import asyncio
from context import Context, InMemoryContextStorage


class MessageRouter:
    def __init__(self, _scheduler):
        self.routes = {} # routes are for persistant routing of messages by type
        self.await_routes = {}  # used for one time routing, not horizontally scalable.

        self.scheduler = _scheduler
        self.named_handlers = {}  # Store mapping of handler names to functions, used for state machine like processing.

    def add_route(self, msg_type, handler):
        # allow multiple handler functions to register to the same message type
        if msg_type not in self.routes:
            self.routes[msg_type] = []
        handler_name = handler.__name__
        self.routes[msg_type].append(handler_name)

    # used as a message decorator only. Not currently used in the examples
    def add_message_route(self, msg_type):
        def decorator_route_message(func):
            self.add_route(msg_type, func)
            return func
        return decorator_route_message

    def add_named_handler(self, handler, name):
        # only one handler per name
        self.named_handlers[name] = handler


    # used to engage named routes
    def register_handler(self, from_did, msg_type, handler):
        handler_name = handler.__name__
        self.named_handlers[handler_name] = handler

    # used for await routes
    def wait_for_message(self, from_did, msg_type):
        # Create a new Future object.
        message_future = asyncio.get_running_loop().create_future()

        fingerprint = f"{from_did}|{msg_type}"
        self.await_routes[fingerprint] = message_future

        return message_future  # this can be awaited.

    async def route_message(self, msg):
        msg_type = msg["type"]
        from_did = msg["from"]
        thid = msg.get("thid", None)

        # Get appropriate contexts
        contact_context = InMemoryContextStorage(("contact", from_did))
        #TODO: add thread routing capability
        routing_context = InMemoryContextStorage(("routing", from_did))
        if thid:
            thread_context = InMemoryContextStorage(("thread", from_did, thid))
        else: 
            thread_context = None

        # Check for registered named route
        handler_name = routing_context.get(msg_type)

        if handler_name:
            routing_context.delete(msg_type)
            handler =  self.named_handlers.get(handler_name, None)
            if handler:
                await self.scheduler.spawn(
                    handler(msg, contact_context, thread_context) 
                )
            return

        # check instant routing
        fingerprint = f"{from_did}|{msg_type}"
        if fingerprint in self.await_routes:
            print("Routing ONCE message")
            msg_future = self.await_routes[fingerprint]
            msg_future.set_result((msg, contact_context, thread_context))
            del self.await_routes[fingerprint]  # remove the registered handler
            return  # don't process 'once' messages. This could be optional

        if msg_type in self.routes:
            for handler_name in self.routes[msg_type]:
                handler = self.named_handlers.get(handler_name)
                if handler:
                    await self.scheduler.spawn(
                        handler(msg, contact_context, thread_context)
                    )
        else:
            await self.unknown_handler(msg, contact_context, thread_context)

    async def unknown_handler(self, msg, context, thread_context):
        print("Unknown Message: ", msg)
        print("Context: ", context)
        print("Thread Context: ", thread_context)

