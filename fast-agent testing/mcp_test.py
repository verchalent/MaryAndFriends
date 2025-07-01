import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("Agent Example")

@fast.agent(
    instruction="An AI agent that assists with basic tasks. Request Human Input when needed.",
    human_input=True,
    servers=["wikijs"],
)
async def main():
  async with fast.run() as agent:
    await agent()

if __name__ == "__main__":
    asyncio.run(main())