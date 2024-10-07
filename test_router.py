import unittest
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

class TestMessageRouter(unittest.TestCase):
    def setUp(self):
        self.router = MessageRouter(None)  # Passing None as scheduler for now

    def test_add_route(self):
        def test_handler(msg, context):
            pass
        self.router.add_route("test_type", test_handler)
        self.assertIn("test_type", self.router.routes)
        self.assertEqual(self.router.routes["test_type"][0], "test_handler")

    def test_register_handler(self):
        def test_handler(msg, context):
            pass
        self.router.register_handler("did1", "msg_type1", test_handler)
        self.assertEqual(
            self.router.named_function_handler.get_handler("did1", "msg_type1"),
            "test_handler"
        )

if __name__ == '__main__':
    unittest.main()