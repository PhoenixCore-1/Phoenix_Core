from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class AICapability(str, Enum):
    ASK = "ask"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    RECOMMEND = "recommend"
    CLASSIFY = "classify"
    PREDICT = "predict"
    DETECT = "detect"
    GENERATE = "generate"
    PROPOSE_ACTION = "propose_action"
    EXECUTE_ACTION = "execute_action"


class AIRequestMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


@dataclass(frozen=True)
class AIContext:
    """
    Provider-neutral, authorized context supplied to an AI request.

    Context must already be restricted to information the requesting
    identity is authorized to access.
    """
    items: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIActionRequest:
    """
    Provider-neutral representation of a proposed or requested business action.

    AI does not execute business state changes directly. The owning module
    application service remains authoritative for validation and execution.
    """
    action_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    target_type: Optional[str] = None
    target_id: Optional[str] = None


@dataclass(frozen=True)
class AIRequest:
    """
    Canonical Phoenix AI request contract.

    Provider-specific request formats must be translated to/from this
    contract by Core provider adapters.
    """
    capability: AICapability
    prompt: str
    context: AIContext = field(default_factory=AIContext)
    mode: AIRequestMode = AIRequestMode.SYNC
    action: Optional[AIActionRequest] = None
    model: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIUsage:
    """
    Provider-neutral usage information.

    Providers may expose different usage measurements. Adapters normalize
    available measurements into this structure.
    """
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    currency: Optional[str] = None


@dataclass(frozen=True)
class AIResponse:
    """
    Canonical Phoenix AI response contract.
    """
    capability: AICapability
    content: str
    provider: str
    model: str
    usage: Optional[AIUsage] = None
    action_proposal: Optional[AIActionRequest] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIError:
    """
    Provider-neutral representation of an AI execution failure.
    """
    code: str
    message: str
    retryable: bool = False
    provider: Optional[str] = None


__all__ = [
    "AICapability",
    "AIRequestMode",
    "AIContext",
    "AIActionRequest",
    "AIRequest",
    "AIUsage",
    "AIResponse",
    "AIError",
]
