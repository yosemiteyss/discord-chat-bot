from typing import List

from src.model.model import Model

OPENAI_MODELS: List[Model] = [
    Model(name='gpt-3.5-turbo'),
    Model(name='gpt-3.5-turbo-16k'),
    Model(name='gpt-4'),
    Model(name='gpt-4-32k'),
    Model(name='gpt-4-vision-preview', upload_image=True)
]

AZURE_MODELS: List[Model] = [
    Model(name='gpt-35-turbo'),
    Model(name='gpt-35-turbo-16k'),
    Model(name='gpt-4'),
    Model(name='gpt-4-32k')
]

GENAI_MODELS: List[Model] = [
    Model(name='models/gemini-pro'),
]
