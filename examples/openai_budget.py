"""
Example: OpenAI Budget Protection
Shows how to protect OpenAI API calls from overspending
"""
from hexarch_guardrails import Guardian

# Initialize guardrails
guardian = Guardian()

# Example 1: Simple decorator
@guardian.check("api_budget")
def call_openai_gpt4(prompt: str) -> str:
    """
    This would call OpenAI, but guardrails check budget first
    """
    import openai
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# Example 2: With context
@guardian.check("api_budget", context={"model": "gpt-4", "tokens": 500})
def expensive_analysis(data: str) -> dict:
    """Analyze data with context about cost"""
    import openai
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Analyze: {data}"}]
    )


if __name__ == "__main__":
    print("Hexarch Guardrails - OpenAI Budget Protection Example")
    print("=" * 50)
    print(f"✓ Guardian initialized")
    print(f"✓ Available policies: {guardian.list_policies()}")
    print()
    print("To use:")
    print("  from examples.openai_budget import call_openai_gpt4")
    print("  response = call_openai_gpt4('Your prompt')")
    print()
    print("The guardian will check your monthly budget before")
    print("allowing the API call to execute.")
