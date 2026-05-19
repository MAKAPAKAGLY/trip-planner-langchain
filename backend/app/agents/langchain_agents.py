"""LangChain Agent 模块

基于 LangChain v1 / LangGraph 框架的智能体实现。
使用 langchain.agents.create_agent 创建 Agent，
通过 ChatOpenAI 驱动 LLM 调用，支持工具调用和多轮推理。

新增: ReActStepCallback — 带线程锁, 多 Agent 并行输出不会交错
"""
import logging
import sys
import threading
from typing import Optional, Any
from uuid import UUID

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)

logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# ── 终端颜色 ──
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_YELLOW = "\033[33m"
C_GREEN  = "\033[32m"
C_BLUE   = "\033[34m"
C_CYAN   = "\033[36m"
C_GRAY   = "\033[90m"

# ── 全局线程锁，确保多 Agent 并行时终端输出不会交错 ──
_print_lock = threading.Lock()


def _safe_print(*args, **kwargs):
    """线程安全的 print，每次调用完整输出一行不被其他线程打断"""
    with _print_lock:
        print(*args, **kwargs)


class ReActStepCallback(BaseCallbackHandler):
    """ReAct 循环回调 — 在终端打印 Thought / Action / Observation

    每一轮 LLM 调用对应:
      Thought: LLM 开始思考 (on_llm_start)
      Action:  LLM 决定调用工具 (on_tool_start)
      Observation: 工具返回结果 (on_tool_end)

    如果 LLM 不调工具直接输出文本, 那就是 Final Answer。
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.round = 0
        self.tool_count = 0
        self._saw_tool_call = False

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str],
        *, run_id: UUID, parent_run_id: UUID | None = None,
        tags: list[str] | None = None, metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.round += 1
        self._saw_tool_call = False
        _safe_print(
            f"\n{C_GRAY}{'─'*50}{C_RESET}\n"
            f"  [{self.agent_name}] "
            f"{C_BOLD}{C_BLUE}💭 Thought (Round {self.round}){C_RESET}"
        )

    def on_llm_end(
        self, response, *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        if not self._saw_tool_call:
            content = ""
            if hasattr(response, "generations") and response.generations:
                gen = response.generations[0][0]
                msg = getattr(gen, "message", None)
                if msg and hasattr(msg, "content"):
                    content = msg.content
            preview = content[:200] + "..." if len(content) > 200 else content
            _safe_print(
                f"  [{self.agent_name}] "
                f"{C_BOLD}{C_GREEN}✅ Final Answer{C_RESET} — {preview}"
            )

    def on_tool_start(
        self, serialized: dict[str, Any], input_str: str,
        *, run_id: UUID, parent_run_id: UUID | None = None,
        tags: list[str] | None = None, metadata: dict[str, Any] | None = None,
        inputs_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._saw_tool_call = True
        self.tool_count += 1
        tool_name = serialized.get("name", "unknown")
        args_str = str(inputs_kwargs) if inputs_kwargs else input_str
        if len(args_str) > 150:
            args_str = args_str[:150] + "..."
        _safe_print(
            f"  [{self.agent_name}] "
            f"{C_BOLD}{C_YELLOW}🔧 Action{C_RESET}  → 调用工具 [{tool_name}]({args_str})"
        )

    def on_tool_end(
        self, output: Any, *, run_id: UUID, parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        result_str = str(output)
        if len(result_str) > 300:
            result_str = result_str[:300] + f"... (共 {len(str(output))} 字符)"
        _safe_print(
            f"  [{self.agent_name}] "
            f"{C_BOLD}{C_CYAN}👁️  Observation{C_RESET} ← {result_str}"
        )

    def on_tool_error(
        self, error: BaseException, *, run_id: UUID,
        parent_run_id: UUID | None = None, **kwargs: Any,
    ) -> None:
        _safe_print(
            f"  [{self.agent_name}] "
            f"{C_BOLD}\033[31m❌ Tool Error{C_RESET} — {error}"
        )


def build_agent(
    name: str,
    system_prompt: str,
    model: str,
    api_key: str,
    base_url: str,
    tools: Optional[list] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
):
    """创建一个 LangChain Agent。

    Args:
        name: Agent 名称 (用于日志和终端输出标识)
        system_prompt: 系统提示词
        model: LLM 模型名
        api_key: API key
        base_url: API Base URL
        tools: LangChain 工具列表 (可选, 空列表表示无工具)
        temperature: 模型温度
        max_tokens: 最大输出 token 数

    Returns:
        一个可调用对象，接收 user_query 字符串，返回 Agent 执行结果的字符串。
    """
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    agent = create_agent(
        model=llm,
        tools=tools if tools is not None else [],
        system_prompt=system_prompt,
    )

    callback = ReActStepCallback(name)

    def run(user_query: str) -> str:
        """执行 Agent，返回最终结果文本"""
        try:
            _safe_print(
                f"\n{C_BOLD}══════════════════════════════════════════════{C_RESET}\n"
                f"{C_BOLD}  [{name}] 接收任务:{C_RESET}\n"
                f"  {user_query[:200]}..."
            )
            _safe_print(f"{C_BOLD}══════════════════════════════════════════════{C_RESET}")

            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_query}]},
                config={"callbacks": [callback]},
            )

            messages = result.get("messages", [])
            for msg in reversed(messages):
                content = getattr(msg, "content", "")
                if content and hasattr(msg, "type") and msg.type != "tool":
                    _safe_print(f"\n  [{name}] ✅ 执行完成 ({len(content)} 字符)")
                    return content

            _safe_print(f"  [{name}] ⚠️ 未找到最终响应")
            return "未能获取有效响应"

        except Exception as e:
            _safe_print(f"\n  [{name}] ❌ 执行失败: {e}")
            return f"错误: Agent 执行失败 - {e}"

    return run
