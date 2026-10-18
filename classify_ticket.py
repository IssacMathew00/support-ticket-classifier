
import json
import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

# Load configuration from .env
load_dotenv()

ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
DEPLOYMENT = os.getenv("FOUNDRY_DEPLOYMENT")

if not ENDPOINT or not DEPLOYMENT:
    raise ValueError(
        "Missing FOUNDRY_ENDPOINT or FOUNDRY_DEPLOYMENT in .env"
    )

print("Connecting to Microsoft Foundry...")

# Authenticate using Microsoft Entra ID
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://ai.azure.com/.default",
)

client = OpenAI(
    base_url=ENDPOINT,
    api_key=token_provider,
)


def classify_ticket(subject: str, description: str) -> dict:
    """Classify a support ticket and return category and priority."""

    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": """
You are an IT Service Desk ticket classification assistant.

Classify each ticket into one category:
Access, Hardware, Network, Email, Software, or Other.

Assign one priority:
Low, Medium, High, or Critical.

Priority guidelines:
- Low: Minor issue with little impact.
- Medium: Individual user affected, with a workaround available.
- High: Important service unavailable or significant user impact.
- Critical: Major outage, widespread business disruption,
  or an urgent security incident.

Return only a valid JSON object with exactly these keys:
{
  "category": "one category",
  "priority": "one priority"
}
""",
            },
            {
                "role": "user",
                "content": (
                    f"Subject: {subject}\n"
                    f"Description: {description}"
                ),
            },
        ],
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The model returned an empty response.")

    result = json.loads(content)

    # Validate the JSON structure
    if set(result.keys()) != {"category", "priority"}:
        raise ValueError(f"Unexpected JSON structure: {result}")

    allowed_categories = {
        "Access", "Hardware", "Network", "Email", "Software", "Other"
    }
    allowed_priorities = {"Low", "Medium", "High", "Critical"}

    if result["category"] not in allowed_categories:
        raise ValueError(f"Invalid category: {result['category']}")

    if result["priority"] not in allowed_priorities:
        raise ValueError(f"Invalid priority: {result['priority']}")

    return result


# Three sample support tickets
tickets = [
    {
        "subject": "Unable to log in to company account",
        "description": (
            "My password is rejected even after resetting it. "
            "I cannot access my work applications."
        ),
    },
    {
        "subject": "Laptop running slowly",
        "description": (
            "Applications open slowly and the laptop occasionally "
            "freezes, but I can still complete my work."
        ),
    },
    {
        "subject": "Company-wide email service outage",
        "description": (
            "All employees are unable to send or receive emails. "
            "Multiple departments and business operations are affected."
        ),
    },
]


def main():
    print("\nStarting ticket classification...\n")

    for number, ticket in enumerate(tickets, start=1):
        print(f"Processing ticket {number}: {ticket['subject']}")

        try:
            result = classify_ticket(
                ticket["subject"],
                ticket["description"],
            )

            print(json.dumps(result, indent=2))
            print("-" * 40)

        except Exception as exc:
            print(f"Classification failed: {exc}")
            print("-" * 40)


if __name__ == "__main__":
    main()
