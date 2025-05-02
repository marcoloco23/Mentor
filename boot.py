# mentor/boot.py
from mem0 import MemoryClient
from openai import OpenAI
import os, dotenv, logging
from src.memory import MemoryManager
from src.llm import LLMClient

dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("MentorBoot")

mem0 = MemoryClient(
    os.environ["MEM0_API_KEY"]
)  # ⟵ docs example [oai_citation:0‡docs.mem0.ai](https://docs.mem0.ai/platform/quickstart)
logger.info("Initialized MemoryClient (mem0)")
openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
logger.info("Initialized OpenAI client")

memory_manager = MemoryManager(mem0)
llm_client = LLMClient(openai)
