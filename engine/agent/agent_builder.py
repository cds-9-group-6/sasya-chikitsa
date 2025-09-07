from typing import Tuple

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from engine.agent.llm import create_llm
from engine.agent.tools import ClassificationTools
from engine.agent.emitter import EmitterManager


def build_agents(classifier_tools: ClassificationTools, emitter_mgr: EmitterManager) -> Tuple[RunnableWithMessageHistory, RunnableWithMessageHistory, object]:
    system = (
        "You are a helpful plant diagnostics assistant. "
        "Hold a helpful, concise conversation. "
        "When the user wants to analyze a leaf image, call the `classify_leaf` tool. "
        "Only call `classify_leaf` if and only if has_image is true and system_context contains an image_handle. "
        "Never fabricate an image_handle. If has_image is false, do not call `classify_leaf`. "
        "Use the image_handle provided in the system context if present. "
        "After calling the tool, provide a helpful summary of the results to the user. "
        "You have access to previous classification results from the same session. "
        "Use this information to answer follow-up questions without requiring new images. "
        "If the user asks about previous results or session info, use the `get_session_info` tool."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system + "\nSystem context: {system_context}\nHas image: {has_image}"),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "{input}"),
    ])

    llm = create_llm()

    tools_with = [classifier_tools.classify_leaf]
    tools_without = []

    agent_with = create_tool_calling_agent(llm, tools_with, prompt)
    executor_with = AgentExecutor(agent=agent_with, tools=tools_with, verbose=False, max_iterations=1)

    agent_without = create_tool_calling_agent(llm, tools_without, prompt)
    executor_without = AgentExecutor(agent=agent_without, tools=tools_without, verbose=False, max_iterations=1)

    def get_history(cfg):
        from engine.api.agent_server import AgentServer  # local import to avoid cycles
        sid = cfg.get("configurable", {}).get("session_id", "default") if isinstance(cfg, dict) else "default"
        return AgentServer.instance()._get_session_history(sid)

    with_tool = RunnableWithMessageHistory(
        executor_with,
        get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    no_tool = RunnableWithMessageHistory(
        executor_without,
        get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return with_tool, no_tool, llm


