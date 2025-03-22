import groq
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import re

# -------------------------------------------------------------------
# System Message for the Telugu Conversation Jokes Generator
# -------------------------------------------------------------------
JOKES_SYSTEM_MESSAGE = (
    "You are a Conversation Jokes Generator specialized in producing humorous conversation-style jokes for stand-up comedy. "
    "All output (jokes, dialogues, and explanations) must be generated in Telugu. "
    "Each joke must consist of two dialogues (from two characters) and include a brief explanation of why the joke is funny. "
    "If the user does not provide a topic, choose a random entertaining topic (for example, 'smartphone' or 'wife-husband'). "
    "Also, add fun emojis (😂, 😜, 👍) to enhance the humorous tone. "
    "All instructions and prompts in your responses must be in English."
)

# -------------------------------------------------------------------
# Define the state for the workflow
# -------------------------------------------------------------------
class JokeState(TypedDict):
    input_details: str
    topic: str
    enriched_topic: str
    bulk_jokes: List[dict]   # Each element is a conversation joke (dialogue1, dialogue2, explanation)
    enhanced_jokes: List[dict]
    filtered_jokes: List[dict]
    ordered_jokes: List[dict]
    final_output: str

# -------------------------------------------------------------------
# Define Structured Output Schemas for each node with type and description
# -------------------------------------------------------------------
class TopicExtractionOutput(BaseModel):
    topic: str = Field(
        ...,
        description="(type: str) The topic for generating jokes in Telugu. If the user does not provide a topic, choose a random entertaining topic."
    )

class TopicEnrichmentOutput(BaseModel):
    enriched_topic: str = Field(
        ...,
        description="(type: str) The enriched topic with additional context or related keywords, to guide the joke generation (output must be in Telugu)."
    )

# Conversation joke schema: two dialogues plus explanation.
class ConversationJoke(BaseModel):
    dialogue1: str = Field(
        ...,
        description="(type: str) The first character's dialogue in Telugu."
    )
    dialogue2: str = Field(
        ...,
        description="(type: str) The second character's dialogue in Telugu."
    )
    explanation: str = Field(
        ...,
        description="(type: str) A brief explanation in Telugu of why the joke is funny."
    )

class BulkJokeGenerationOutput(BaseModel):
    bulk_jokes: List[ConversationJoke] = Field(
        ...,
        description="(type: list) A list of 10 to 20 conversation jokes (each with two dialogues and an explanation) in Telugu."
    )

class JokeOptimizationOutput(BaseModel):
    enhanced_jokes: List[ConversationJoke] = Field(
        ...,
        description="(type: list) A list of optimized conversation jokes in Telugu with improved humor, language flow, and punchlines."
    )

class JokeFilteringOutput(BaseModel):
    filtered_jokes: List[ConversationJoke] = Field(
        ...,
        description="(type: list) A list of high-quality conversation jokes in Telugu after filtering out duplicates or low-quality items."
    )

class JokeOrderingOutput(BaseModel):
    ordered_jokes: List[ConversationJoke] = Field(
        ...,
        description="(type: list) An ordered list of conversation jokes (each with two dialogues and an explanation) in Telugu."
    )

class FinalOutputOutput(BaseModel):
    final_output: str = Field(
        ...,
        description="(type: str) The final formatted output containing all the ordered jokes with their explanations, presented as bullet points or a numbered list, in Telugu."
    )

# -------------------------------------------------------------------
# Telugu Conversation Jokes Workflow Class with Structured LLM Outputs
# -------------------------------------------------------------------
class TeluguJokesWorkflow:
    def __init__(self, llm: ChatGroq, verbose: bool = False):
        self.llm: ChatGroq = llm
        self.verbose = verbose
        self.workflow = self._build_workflow()
        # Optionally, generate a workflow diagram:
        # graph_png = self.workflow.get_graph(xray=True).draw_mermaid_png()
        # with open("TeluguJokesWorkflow.png", "wb") as file:
        #     file.write(graph_png)

    def _verbose_print(self, message: str, state=None):
        if self.verbose:
            print(f"\n\033[92m[VERBOSE] {message}\033[0m")
    
    def _get_messages(self, new_message: str):
        messages = [
            SystemMessage(content=JOKES_SYSTEM_MESSAGE),
            HumanMessage(content=new_message)
        ]
        return messages

    def _build_workflow(self):
        builder = StateGraph(JokeState)
        
        builder.add_node('TopicExtraction', self.topic_extraction_node)
        builder.add_node('TopicEnrichment', self.topic_enrichment_node)
        builder.add_node('BulkJokeGeneration', self.bulk_joke_generation_node)
        builder.add_node('JokeOptimization', self.joke_optimization_node)
        builder.add_node('JokeFiltering', self.joke_filtering_node)
        builder.add_node('JokeOrdering', self.joke_ordering_node)
        builder.add_node('FinalOutput', self.final_output_node)
        
        # Set up a sequential flow:
        builder.add_edge(START, 'TopicExtraction')
        builder.add_edge('TopicExtraction', 'TopicEnrichment')
        builder.add_edge('TopicEnrichment', 'BulkJokeGeneration')
        builder.add_edge('BulkJokeGeneration', 'JokeOptimization')
        builder.add_edge('JokeOptimization', 'JokeFiltering')
        builder.add_edge('JokeFiltering', 'JokeOrdering')
        builder.add_edge('JokeOrdering', 'FinalOutput')
        builder.add_edge('FinalOutput', END)
        
        return builder.compile()
    
    def topic_extraction_node(self, state: JokeState) -> dict:
        prompt = (
            f"User Input Details: {state['input_details']}\n"
            "Extract the topic for generating Telugu conversation jokes. "
            "If the user does not specify a topic, choose a random entertaining topic (e.g., wife-husband or smartphone).\n"
            "Return the output in JSON format with the following key:\n"
            "- 'topic' (type: str): The extracted or chosen topic."
        )
        structured_llm = self.llm.with_structured_output(TopicExtractionOutput, method="json_mode")
        response: TopicExtractionOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print(f"Extracted Topic: {response.topic}", state)
        return {"topic": response.topic}
    
    def topic_enrichment_node(self, state: JokeState) -> dict:
        prompt = (
            f"Using the topic '{state['topic']}', enrich the topic with additional context or related keywords to guide the joke generation. "
            "The enriched topic must be suitable for generating conversation jokes in Telugu.\n"
            "Return the output in JSON format with the following key:\n"
            "- 'enriched_topic' (type: str): The enriched topic with extra context or keywords."
        )
        structured_llm = self.llm.with_structured_output(TopicEnrichmentOutput, method="json_mode")
        response: TopicEnrichmentOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print(f"Enriched Topic: {response.enriched_topic}", state)
        return {"enriched_topic": response.enriched_topic}
    
    def bulk_joke_generation_node(self, state: JokeState) -> dict:
        prompt = (
            f"Generate between 10 to 20 conversation-style jokes in Telugu on the topic '{state['enriched_topic']}'. "
            "Each joke should consist of two dialogues (dialogue1 and dialogue2) from two different characters, "
            "and include a brief explanation of why the joke is funny. Also, add fun emojis (😂, 😜, 👍) for extra liveliness.\n"
            "Return the output in JSON format with the following key:\n"
            "- 'bulk_jokes' (type: list): A list of joke objects, each with 'dialogue1', 'dialogue2', and 'explanation'."
        )
        structured_llm = self.llm.with_structured_output(BulkJokeGenerationOutput, method="json_mode")
        response: BulkJokeGenerationOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print(f"Generated {len(response.bulk_jokes)} jokes", state)
        return {"bulk_jokes": [j.dict() for j in response.bulk_jokes]}
    
    def joke_optimization_node(self, state: JokeState) -> dict:
        prompt = (
            "Optimize the following conversation jokes to improve their humor, dialogue flow, and punchlines. "
            "Ensure that all jokes remain in Telugu and include fun emojis for emphasis.\n"
            f"Jokes:\n{state['bulk_jokes']}\n"
            "Return the output in JSON format with the following key:\n"
            "- 'enhanced_jokes' (type: list): A list of optimized joke objects."
        )
        structured_llm = self.llm.with_structured_output(JokeOptimizationOutput, method="json_mode")
        response: JokeOptimizationOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print(f"Optimized {len(response.enhanced_jokes)} jokes", state)
        return {"enhanced_jokes": [j.dict() for j in response.enhanced_jokes]}
    
    def joke_filtering_node(self, state: JokeState) -> dict:
        prompt = (
            f"Filter out duplicate or low-quality jokes from the following list:\n{state['enhanced_jokes']}\n"
            "Return only the high-quality jokes in Telugu in JSON format with the following key:\n"
            "- 'filtered_jokes' (type: list): A list of filtered joke objects."
        )
        structured_llm = self.llm.with_structured_output(JokeFilteringOutput, method="json_mode")
        response: JokeFilteringOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print(f"Filtered down to {len(response.filtered_jokes)} jokes", state)
        return {"filtered_jokes": [j.dict() for j in response.filtered_jokes]}
    
    def joke_ordering_node(self, state: JokeState) -> dict:
        prompt = (
            f"Organize and order the following jokes into a coherent sequence for performance:\n{state['filtered_jokes']}\n"
            "Return the ordered jokes in JSON format with the following key:\n"
            "- 'ordered_jokes' (type: list): An ordered list of joke objects."
        )
        structured_llm = self.llm.with_structured_output(JokeOrderingOutput, method="json_mode")
        response: JokeOrderingOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print(f"Ordered {len(response.ordered_jokes)} jokes", state)
        return {"ordered_jokes": [j.dict() for j in response.ordered_jokes]}
    
    def final_output_node(self, state: JokeState) -> dict:
        prompt = (
            "Consolidate the following ordered jokes into a final formatted output. "
            "Format the output as bullet points or a numbered list, showing each joke's dialogues and its explanation after each joke.\n"
            f"Jokes:\n{state['ordered_jokes']}\n"
            "Return the output in JSON format with the following key:\n"
            "- 'final_output' (type: str): The final formatted output containing all the jokes and their explanations in Telugu."
        )
        structured_llm = self.llm.with_structured_output(FinalOutputOutput, method="json_mode")
        response: FinalOutputOutput = structured_llm.invoke(self._get_messages(prompt))
        self._verbose_print("Final Output generated.", state)
        return {"final_output": response.final_output}
    
    def run(self, input_details: str) -> str:
        self._verbose_print(f"Running Telugu Jokes Workflow with input: {input_details}")
        initial_state: JokeState = {
            "input_details": input_details,
            "topic": "",
            "enriched_topic": "",
            "bulk_jokes": [],
            "enhanced_jokes": [],
            "filtered_jokes": [],
            "ordered_jokes": [],
            "final_output": ""
        }
        final_state = self.workflow.invoke(initial_state)
        return final_state["final_output"]

# ------------------------------------------------------------------------------
# Example Usage:
#
llm_instance = ChatGroq(model='deepseek-r1-distill-llama-70b')
workflow = TeluguJokesWorkflow(llm_instance, verbose=True)
user_input = "I need jokes for a prerecorded YouTube video on the wife-husband topic."
final_output = workflow.run(user_input)
print("Final Telugu Conversation Jokes Output:\n", final_output)
