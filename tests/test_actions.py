import time
import unittest

from actionflow.action import Action
from actionflow.actions.examples import (
    BlockingAction1,
    BlockingAction2,
    NonBlockingAction,
)


class TestRegistry(unittest.TestCase):
    def test_from_string(self):
        yaml_content = """
        upgrade:
          steps:
            - name: download
              with:
                url: http://example.com
                timeout: 30
        """

        actions = Action.from_string(yaml_content)

        # self.assertIn("download", registry.actions)

        action = actions._items[0]
        self.assertIsInstance(action, Action)
        self.assertEqual(action.name, "download")
        self.assertEqual(action.url, "http://example.com")
        self.assertEqual(action.timeout, 30)

        self.assertEqual(actions.grouped, [[action]])

    def test_custom_actions(self):
        class CustomAction(Action):
            name: str = "custom"
            description: str = "Custom action"
            time: int = 1

            def _run(self):
                logging.info(f"Running {self.name} for {self.time} seconds")
                time.sleep(self.time)
                return True

        content = {
            "upgrade": {
                "steps": [
                    {
                        "name": "sample-non-blocking",
                    },
                    {
                        "name": "sample-blocking-1",
                    },
                    {
                        "name": "sample-blocking-2",
                    },
                ]
            }
        }

        actions = Actions(content)
        NonBlockingAction, BlockingAction1, BlockingAction2
        action_results = actions.run_in_threads()
        logging.info(action_results)

        # action = CustomAction()
        # self.assertEqual(action.run(), True)
        # self.assertIsInstance(action, Action)


if __name__ == "__main__":
    unittest.main()
