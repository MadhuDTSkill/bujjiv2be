from langchain.memory import ConversationSummaryBufferMemory
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage

llm = ChatGroq(model='gemma2-9b-it')


memory = ConversationSummaryBufferMemory(
    llm=llm, max_token_limit=10
)

memory.chat_memory.add_messages([
    SystemMessage(content =''),
    HumanMessage(content="What are the skill of rakesh ?"),
    AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_8jnd', 'function': {'arguments': '{"query":"What are the skills of rakesh"}', 'name': 'Vector DB'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 87, 'prompt_tokens': 961, 'total_tokens': 1048, 'completion_time': 0.158181818, 'prompt_time': 0.041102431, 'queue_time': 0.233914917, 'total_time': 0.199284249}, 'model_name': 'gemma2-9b-it', 'system_fingerprint': 'fp_10c08bf97d', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-096d28d9-9d10-4e24-a8db-36bd9aef8e2f-0', tool_calls=[{'name': 'Vector DB', 'args': {'query': 'What are the skills of rakesh'}, 'id': 'call_8jnd', 'type': 'tool_call'}], usage_metadata={'input_tokens': 961, 'output_tokens': 87, 'total_tokens': 1048}),
    ToolMessage(content="""
        Here is the vector DB Doc similar chunks

        1 Chunk
        Proficient in Python, JavaScript, and SQL.
        2 Chunk
        Experienced with frameworks like Django, FastAPI, and React.
        3 Chunk
        Skilled in DevOps tools including Docker, Kubernetes, and GitHub Actions.
        4 Chunk
        Developed a real-time chat application using FastAPI and WebSockets.
        5 Chunk
        Software Engineer at ABC Tech (2020-2023), worked on microservice architecture.    
                
    """, tool_call_id = "tension"),
    AIMessage(content='Rakesh is proficient in Python, JavaScript, and SQL. He is also experienced with frameworks like Django, FastAPI, and React. He is skilled in DevOps tools including Docker, Kubernetes, and GitHub Actions.  He developed a real-time chat application using FastAPI and WebSockets and worked as a Software Engineer at ABC Tech. \n', additional_kwargs={}, response_metadata={'token_usage': {'completion_tokens': 71, 'prompt_tokens': 1141, 'total_tokens': 1212, 'completion_time': 0.129090909, 'prompt_time': 0.039925584, 'queue_time': 0.23535983099999996, 'total_time': 0.169016493}, 'model_name': 'gemma2-9b-it', 'system_fingerprint': 'fp_10c08bf97d', 'finish_reason': 'stop', 'logprobs': None}, id='run-88d7968b-e7f4-4076-b1fa-da8cffb7a53a-0', usage_metadata={'input_tokens': 1141, 'output_tokens': 71, 'total_tokens': 1212}),
   
])

print(memory.load_memory_variables({}))
