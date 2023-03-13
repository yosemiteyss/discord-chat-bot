from dataclasses import dataclass
from datetime import datetime
from typing import List
from aiohttp import ClientSession

from src.constants import OPENAI_API_KEY


@dataclass(frozen=True)
class Usage:
    aggregation_timestamp: int
    n_requests: int
    operation: str
    snapshot_id: str
    n_context: int
    n_context_tokens_total: int
    n_generated: int
    n_generated_tokens_total: int


async def get_usage() -> List[Usage]:
    async with ClientSession() as session:
        async with session.get(
                'https://api.openai.com/v1/usage',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}'
                },
                params={
                    'date': datetime.today().strftime('%Y-%m-%d')
                }
        ) as response:
            usage_res = await response.json()
            return [Usage(**data) for data in usage_res['data']]
