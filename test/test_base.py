from unittest import TestCase

from src.model.conversation import Conversation
from src.model.message import Message
from src.model.prompt import Prompt
from src.model.role import Role


class BaseTest(TestCase):

    def test_render_message(self):
        message = Message(
            role=Role.USER.value,
            content="New synergies will help drive top-line growth."
        )
        expected = {
            "role": "user",
            "content": "New synergies will help drive top-line growth."
        }
        self.assertDictEqual(message.render(), expected)

    def test_render_conversation(self):
        convo = Conversation(
            messages=[
                Message(
                    role=Role.USER.value,
                    content="Help me translate the following corporate jargon into plain English."
                ),
                Message(
                    role=Role.ASSISTANT.value,
                    content="Sure, I'd be happy to!"
                )
            ]
        )
        expected = [
            {"role": "user", "content": "Help me translate the following corporate jargon into plain English."},
            {"role": "assistant", "content": "Sure, I'd be happy to!"},
        ]
        self.assertListEqual(convo.render(), expected)

    def test_render_prompt(self):
        prompt = Prompt(
            header=Message(
                role=Role.SYSTEM.value,
                content="You are a helpful, pattern-following assistant."
            ),
            conversation=Conversation(
                messages=[
                    Message(
                        role=Role.USER.value,
                        content="Help me translate the following corporate jargon into plain English."
                    ),
                    Message(
                        role=Role.ASSISTANT.value,
                        content="Sure, I'd be happy to!"
                    )
                ]
            )
        )
        expected = [
            {"role": "system", "content": "You are a helpful, pattern-following assistant."},
            {"role": "user", "content": "Help me translate the following corporate jargon into plain English."},
            {"role": "assistant", "content": "Sure, I'd be happy to!"},
        ]
        self.assertListEqual(prompt.render(), expected)
