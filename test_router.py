import unittest
import asyncio
from router import NamedFunctionHandler, MessageRouter


class TestNamedFunctionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = NamedFunctionHandler()

    def test_register_and_get_handler(self):
        self.handler.register("did1", "msg_type1", "handler1")
        self.assertEqual(self.handler.get_handler("did1", "msg_type1"), "handler1")

    def test_remove_handler(self):
        self.handler.register("did1", "msg_type1", "handler1")
        self.handler.remove_handler("did1", "msg_type1")
        self.assertIsNone(self.handler.get_handler("did1", "msg_type1"))


class TestMessageRouter(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.scheduler = MockScheduler()
        self.router = MessageRouter(self.scheduler)

    async def test_add_route_and_route_message(self):
        async def test_handler(msg, context):
            return "Handled"

        self.router.add_route("test_type", test_handler)
        msg = {"type": "test_type", "from": "did1"}
        await self.router.route_message(msg)
        self.assertEqual(len(self.scheduler.spawned), 1)

    async def test_register_handler_and_route_message(self):
        async def test_handler(msg, context):
            return "Handled"

        self.router.register_handler("did1", "test_type", test_handler)
        msg = {"type": "test_type", "from": "did1"}
        await self.router.route_message(msg)
        self.assertEqual(len(self.scheduler.spawned), 1)

    async def test_unknown_handler(self):
        msg = {"type": "unknown_type", "from": "did1"}
        await self.router.route_message(msg)
        self.assertEqual(len(self.scheduler.spawned), 0)


class MockScheduler:
    def __init__(self):
        self.spawned = []

    async def spawn(self, coro):
        result = await coro
        self.spawned.append(result)


if __name__ == '__main__':
    unittest.main()