from unittest import TestCase

from src.model.message import Message
from src.model.prompt import Prompt
from src.model.role import Role
from src.service.chat_service import ChatService
from src.service.openai_service import OpenAIService


class OpenAIServiceTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chat_service: ChatService = OpenAIService()

    def test_render_message(self):
        message = Message(
            role=Role.USER.value,
            content="New synergies will help drive top-line growth."
        )
        expected = {
            "role": "user",
            "content": "New synergies will help drive top-line growth."
        }
        self.assertDictEqual(self.chat_service.render_message(message), expected)

        message = Message(
            role=Role.ASSISTANT.value,
            content="Sure, I'd be happy to!"
        )
        expected = {
            "role": "assistant",
            "content": "Sure, I'd be happy to!"
        }
        self.assertDictEqual(self.chat_service.render_message(message), expected)

    def test_build_prompt(self):
        history = [
            Message(
                role=Role.USER.value,
                content="Help me translate the following corporate jargon into plain English."
            ),
            Message(
                role=Role.ASSISTANT.value,
                content="Sure, I'd be happy to!"
            ),
            None
        ]

        prompt = self.chat_service.build_prompt(history)

        self.assertEqual(prompt.header.role, Role.SYSTEM.value)

        self.assertEqual(len(prompt.conversation), 2)
        self.assertEqual(prompt.conversation[0].role, Role.USER.value)
        self.assertEqual(prompt.conversation[1].role, Role.ASSISTANT.value)

        self.assertEqual(
            prompt.conversation[0].content,
            "Help me translate the following corporate jargon into plain English."
        )
        self.assertEqual(
            prompt.conversation[1].content,
            "Sure, I'd be happy to!"
        )

    def test_render_prompt(self):
        prompt = Prompt(
            header=Message(
                role=Role.SYSTEM.value,
                content="You are a helpful, pattern-following assistant."
            ),
            conversation=[
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
            {"role": "system", "content": "You are a helpful, pattern-following assistant."},
            {"role": "user", "content": "Help me translate the following corporate jargon into plain English."},
            {"role": "assistant", "content": "Sure, I'd be happy to!"},
        ]
        self.assertListEqual(self.chat_service.render_prompt(prompt), expected)
