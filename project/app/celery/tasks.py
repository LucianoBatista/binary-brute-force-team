from celery import shared_task
from project.app.agents.simple_agent import run_simple_agent
import asyncio


@shared_task(bind=True, name="project.app.celery.tasks.run_agent_async")
def run_agent_async(self, query: str):
    """
    Celery task for asynchronous agent execution.

    This task wraps the async LangGraph agent workflow so it can be
    executed asynchronously via Celery. Useful for long-running agent
    workflows that shouldn't block HTTP requests.

    Args:
        query: User's input query to process

    Returns:
        Final result from the agent workflow
    """
    try:
        # Create new event loop for the task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the async agent
        result = loop.run_until_complete(run_simple_agent(query))

        loop.close()

        return result

    except Exception as e:
        # Log error and re-raise for Celery to handle
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
