import logging
from langchain_openai import ChatOpenAI
from app.config import settings
from core.langfuse_client import langfuse

logger = logging.getLogger(__name__)
logger.info("Initializing OpenAI LLM")

llm = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0.7
)

class LLMService:
    def __init__(self):
        self.llm = llm

    def generate(self, prompt: str) -> str:
        # Generate a text response from OpenAI and log the call to Langfuse.
        trace = langfuse.trace(name="llm.generate", input={"prompt": prompt})
        try:
            generation = trace.generation(
                name="openai.chat",
                model="gpt-4o-mini",
                input=prompt,
            )

            response = self.llm.invoke(prompt)
            output = response.content

            generation.end(output=output)
            trace.update(output={"response": output})

            return output
        except Exception as e:
            trace.update(status="error", status_message=str(e))
            raise
