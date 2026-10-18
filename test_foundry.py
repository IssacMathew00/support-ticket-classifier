
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

load_dotenv()

endpoint = os.environ["FOUNDRY_ENDPOINT"]
deployment = os.environ["FOUNDRY_DEPLOYMENT"]

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://ai.azure.com/.default",
)

client = OpenAI(
    base_url=endpoint,
    api_key=token_provider,
)

response = client.chat.completions.create(
    model=deployment,
    messages=[
        {"role": "user", "content": "Reply with exactly: Foundry connection successful"}
    ],
    reasoning_effort="low",
)

print(response.choices[0].message.content)
