# ProxyGPT

## Quickstart

Use [ngrok](https://ngrok.com/) to generate a public URL for your local server:

```ngrok http 8080```

Now, add your `ADMIN_TOKEN` and `OPENAI_API_KEYS` (comma-separated) to your .env. Then, run the application:

```docker-compose up --build```

Use your `ADMIN_TOKEN` to generate a key for a user by requesting it from the `/generate_key` endpoint. Finally, users can start sending requests. Depending on the OpenAI SDK version, requests will look like this:

```python
import openai

openai.api_key = "key"
openai.base_url = "http://example.ngrok.app/v1/"

completion = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "What is a Turing machine?"},
    ],
)

print(completion.choices[0].message.content)
```

Or this:

```python
from openai import OpenAI
import json

client = OpenAI(base_url="https://example.ngrok.app/v1",
                api_key="key")

response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[{"role": "user", "content": "What is a Turing machine?"}],
  stream=False
)

print(response.choices[0].message.content)
```

The proxy supports streaming as well:

```python
from openai import AsyncOpenAI
import asyncio
import json

client = AsyncOpenAI(base_url="https://example.ngrok.app/v1",
                api_key="key")

async def main(message: str):
  response = await client.chat.completions.create(
    model="gpt-3.5-turbo",
    temperature=0.7,
    messages=[{"role": "user", "content": message}],
    stream=True
  )
  async for message in response:
    if message.choices[0].delta.content:
      print(message.choices[0].delta.content, end="", flush=True)

asyncio.run(main("What is a Turing machine?"))
```

## todos
- [ ] add more openai endpoints
- [ ] add a queue based on openai's account rate limits
- [ ] add caching of requests
- [ ] more efficient redis queries