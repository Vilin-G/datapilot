import json
import sys, importlib
from openai import OpenAI
import os


sys.path.insert(0, "scripts")
t = importlib.import_module("07_tools")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",

)

tools = [
        {
            "type": "function",
            "function": {
                "name": "describe_database",
                "description": "List tables, column names, column types, row counts, and sample data in the database.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": "Run a SQL query on the database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "The SQL query to run.",
                        },
                    },
                    "required": ["sql"],
                },
            },
        }
    ]


messages = [{"role": "user", "content": "列出数据库里的表"}]
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)
messages.append(response.choices[0].message)

tc = response.choices[0].message.tool_calls[0]

name = tc.function.name
args = json.loads(tc.function.arguments)

if name == "describe_database":
    result = t.describe_database.invoke(args)
elif name == "query_database":
    result = t.query_database.invoke(args)

messages.append(
    {
        "role": "tool",
        "tool_call_id": tc.id,
        "content": result,
    }
)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)


print(response.choices[0].message)











































