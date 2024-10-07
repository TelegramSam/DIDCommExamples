import asyncio
from context import Context, InMemoryContextStorage


class NamedFunctionHandler:
    def __init__(self):
        self.registered_handlers = {}

    def register(self, from_did, msg_type, handler_name):
        key = f"{from_did}|{msg_type}"
        self.registered_handlers[key] = handler_name

    def get_handler(self, from_did, msg_type):
        key = f"{from_did}|{msg_type}"
        return self.registered_handlers.get(key)

    def remove_handler(self, from_did, msg_type):
        key = f"{from_did}|{msg_type}"
        if key in self.registered_handlers:
            del self.registered_handlers[key]


class MessageRouter:
    def __init__(self, _scheduler):
        self.routes = {}
        self.did_type = {}  # used for one time routing
        self.scheduler = _scheduler
        self.context = Context(InMemoryContextStorage())
        self.named_function_handler = NamedFunctionHandler()
        self.handler_map = {}  # Store mapping of handler names to functions

    def add_route(self, msg_type, handler):
        if msg_type not in self.routes:
            self.routes[msg_type] = []
        handler_name = handler.__name__
        self.routes[msg_type].append(handler_name)
        self.handler_map[handler_name] = handler

    def add_message_route(self, msg_type):
        def decorator_route_message(func):
            self.add_route(msg_type, func)
            return func
        return decorator_route_message

    def register_handler(self, from_did, msg_type, handler):
        handler_name = handler.__name__
        self.named_function_handler.register(from_did, msg_type, handler_name)
        self.handler_map[handler_name] = handler

    async def route_message(self, msg):
        msg_type = msg["type"]
        from_did = msg["from"]
        thid = msg.get("thid")

        # Get or create context
        context = self.context.get(from_did)
        if context is None:
            self.context.set(from_did, {})
            context = self.context.get(from_did)

        # Get or create thread context if thid is present
        thread_context = None
        if thid:
            thread_context = self.context.get(thid)
            if thread_context is None:
                self.context.set(thid, {})
                thread_context = self.context.get(thid)

        # Check for registered handler
        handler_name = self.named_function_handler.get_handler(
            from_did, msg_type
        )
        if handler_name:
            self.named_function_handler.remove_handler(from_did, msg_type)
            handler = self.handler_map.get(handler_name)
            if handler:
                await self.scheduler.spawn(
                    handler(msg, context, thread_context)
                )
            return

        # check instant routing
        fingerprint = f"{from_did}|{msg_type}"
        if fingerprint in self.did_type:
            print("Routing ONCE message")
            msg_future = self.did_type[fingerprint]
            msg_future.set_result((msg, context, thread_context))
            del self.did_type[fingerprint]  # remove the registered handler
            return  # don't process 'once' messages. This could be optional

        if msg_type in self.routes:
            for handler_name in self.routes[msg_type]:
                handler = self.handler_map.get(handler_name)
                if handler:
                    await self.scheduler.spawn(
                        handler(msg, context, thread_context)
                    )
        else:
            await self.unknown_handler(msg, context, thread_context)

    async def unknown_handler(self, msg, context, thread_context):
        print("Unknown Message: ", msg)
        print("Context: ", context)
        print("Thread Context: ", thread_context)

    def wait_for_message(self, from_did, msg_type):
        # Create a new Future object.
        message_future = asyncio.get_running_loop().create_future()

        fingerprint = f"{from_did}|{msg_type}"
        self.did_type[fingerprint] = message_future

        return message_future  # this can be awaited.