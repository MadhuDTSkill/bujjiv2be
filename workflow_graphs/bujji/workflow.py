from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from .schemas import WorkFlowState
from .nodes import init_node, load_tools, load_model, load_memory, call_self_discussion, call_model, tool_node, pick_tool_messages, save_messages_to_memory




workflow = StateGraph(WorkFlowState)

workflow.add_node('init', init_node)
workflow.add_node('load_tools', load_tools)
workflow.add_node('load_model', load_model)
workflow.add_node('load_memory', load_memory)
workflow.add_node('call_self_discussion', call_self_discussion)
workflow.add_node('call_model', call_model)
workflow.add_node('tool_node', tool_node)
workflow.add_node('pick_tool_messages', pick_tool_messages)

workflow.add_node('save_messages_to_memory', save_messages_to_memory)

workflow.set_entry_point('init')
workflow.set_finish_point('save_messages_to_memory')

workflow.add_edge('init', 'load_tools')
workflow.add_edge('load_tools', 'load_model')
workflow.add_edge('load_model', 'load_memory')
workflow.add_edge('call_self_discussion', 'call_model')
workflow.add_edge('tool_node', 'pick_tool_messages')
workflow.add_edge('pick_tool_messages', 'call_model')


workflow.add_conditional_edges('load_memory', lambda stage : 'make_dicussion' if stage['self_discussion'] else 'no_dicussion', {'make_dicussion' : 'call_self_discussion', 'no_dicussion' : 'call_model'})
workflow.add_conditional_edges('call_model', tools_condition, {'tools' : 'tool_node', '__end__' : 'save_messages_to_memory'})

graph = workflow.compile()

# Visualize your graph
# graph_png = graph.get_graph(xray=True).draw_mermaid_png(max_retries = 5, retry_delay=2)
# image_file = "GPT-Suite WorkFlow Graph.png"
# with open(image_file, "wb") as file:
#     file.write(graph_png)
