from dataclasses import dataclass
from datetime import datetime
from typing import List

from aiohttp import ClientSession
from discord import Embed, Color
from tiktoken import encoding_for_model, get_encoding

from src.base import Message
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


async def get_usage_embed_message(fetch_credit_grants: bool = False) -> Embed:
    usage_list: List[Usage] = await get_usage()
    total_requests = 0
    total_tokens = 0
    total_generated_tokens = 0

    today = datetime.today().strftime('%Y-%m-%d')
    description = ''

    # Calculate total usage
    for usage in usage_list:
        total_requests += usage.n_requests
        total_tokens += usage.n_context_tokens_total
        total_generated_tokens += usage.n_generated_tokens_total

    # Fetch credit grants
    if fetch_credit_grants:
        credit_grants = await get_credit_grants()
        used_amount = round(credit_grants.used_amount, 2)
        grant_amount = round(credit_grants.grant_amount, 2)
        description = description + f"Credits: ${used_amount} / ${grant_amount}\n"

    description = description + f"""
        Number of requests: {total_requests}
        Number of prompts: {total_tokens}
        Number of completion: {total_generated_tokens}"""

    return Embed(
        title=f"📊 Data Usage of {today}",
        description=description,
        color=Color.fuchsia(),
    )


def count_token_usage(messages: List[Message], model: str = "gpt-3.5-turbo-0301") -> int:
    try:
        encoding = encoding_for_model(model)
    except KeyError:
        encoding = get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.render().items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}. See 
        https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to 
        tokens.""")
