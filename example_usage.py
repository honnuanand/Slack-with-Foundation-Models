#!/usr/bin/env python3
"""
Simple example showing how to use Databricks Foundation Models
with OpenAI-compatible API format
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client with Databricks endpoint
client = OpenAI(
    api_key=os.environ.get("DATABRICKS_TOKEN"),
    base_url=f"{os.environ.get('DATABRICKS_HOST')}/serving-endpoints"
)

# Prepare messages
messages = [
    {"role": "user", "content": "What is machine learning in simple terms?"}
]

# Call Databricks Foundation Model (Llama 4 Maverick)
print("Calling Databricks Foundation Model: Llama 4 Maverick")
print("-" * 60)

response = client.chat.completions.create(
    model="databricks-llama-4-maverick",
    messages=messages,
    max_tokens=500,
    temperature=0.7
)

print(f"Response: {response.choices[0].message.content}")
print("-" * 60)
