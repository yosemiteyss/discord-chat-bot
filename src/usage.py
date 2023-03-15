from asyncio import gather
from dataclasses import dataclass
from datetime import datetime
from typing import List

from aiohttp import ClientSession
from discord import Embed, Color

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


@dataclass(frozen=True)
class CreditGrants:
    object: str
    id: str
    grant_amount: float
    used_amount: float
    effective_at: int
    expires_at: int


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


async def get_credit_grants() -> CreditGrants:
    async with ClientSession() as session:
        async with session.get(
                "https://api.openai.com/dashboard/billing/credit_grants",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}'
                }
        ) as response:
            credit_res = await response.json()
            grants_data = credit_res['grants']['data'][0]
            return CreditGrants(**grants_data)


async def get_usage_embed_message() -> Embed:
    results = await gather(get_usage(), get_credit_grants())
    usage_list: List[Usage] = results[0]
    credit_grants: CreditGrants = results[1]

    total_requests = 0
    total_tokens = 0
    total_generated_tokens = 0

    for usage in usage_list:
        total_requests += usage.n_requests
        total_tokens += usage.n_context_tokens_total
        total_generated_tokens += usage.n_generated_tokens_total

    used_amount = round(credit_grants.used_amount, 2)
    grant_amount = round(credit_grants.grant_amount, 2)

    today = datetime.today().strftime('%Y-%m-%d')

    return Embed(
        title=f"📊 Data Usage of {today}",
        description=f"""Credits: ${used_amount} / ${grant_amount}
                    Number of requests: {total_requests}
                    Number of prompts: {total_tokens}
                    Number of completion: {total_generated_tokens}""",
        color=Color.fuchsia(),
    )
