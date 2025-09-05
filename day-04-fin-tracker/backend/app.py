import asyncio
import parlant.sdk as p

async def create_weekly_savings_journey(agent: p.Agent):
    journey = await agent.create_journey(
        title="Weekly Savings Setup",
        conditions=["User wants to set a savings goal for this week"],
        description="Helps user define and track a weekly savings target."
    )

    # Initial prompt—ask for goal
    t1 = await journey.initial_state.transition_to(
        chat_state="What's your savings target for this week (e.g., $20)?"
    )

    # After user specifies an amount
    t2 = await t1.target.transition_to(
        chat_state="How much have you saved so far this week?"
    )

    # If they've started saving
    t3a = await t2.target.transition_to(
        condition="User entered a positive amount",
        chat_state="Nice job—I’ll help you stay on track."
    )

    # If they haven't saved yet    
    t3b = await t2.target.transition_to(
        condition="User entered zero or didn’t save",
        chat_state="No worries! Want a quick tip to get started?"
    )

    # Final state: encouragement and wrap-up
    await t3a.target.transition_to(
        chat_state="You're on your way—see you tomorrow for a quick check-in!"
    )
    await t3b.target.transition_to(
        chat_state="Let's touch base again soon. You’ve got this!"
    )

    return journey

async def main():
    async with p.Server() as server:
        agent = await server.create_agent(
            name="Weekly Savings Assistant",
            description="Helps users set and track weekly savings goals."
        )
        await create_weekly_savings_journey(agent)

if __name__ == "__main__":
    asyncio.run(main())
