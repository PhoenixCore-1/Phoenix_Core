"""Domain models for Phoenix internal communications."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

class ChannelType(str, Enum):
    DIRECT = "DIRECT"; GROUP = "GROUP"; TEAM = "TEAM"; PROJECT = "PROJECT"; MODULE = "MODULE"; ANNOUNCEMENT = "ANNOUNCEMENT"; CUSTOM = "CUSTOM"
class Visibility(str, Enum):
    PRIVATE = "PRIVATE"; ORG = "ORG"
class MessageStatus(str, Enum):
    ACTIVE = "ACTIVE"; EDITED = "EDITED"; DELETED = "DELETED"
class PresenceStatus(str, Enum):
    ONLINE = "ONLINE"; AWAY = "AWAY"; OFFLINE = "OFFLINE"

@dataclass(frozen=True)
class Channel:
    id: UUID; organisation_id: UUID; channel_type: str; name: str; visibility: str; created_by_identity_id: UUID; status: str; created_at: datetime
@dataclass(frozen=True)
class ChannelMember:
    id: UUID; channel_id: UUID; identity_id: UUID; status: str; joined_at: datetime
@dataclass(frozen=True)
class Conversation:
    id: UUID; organisation_id: UUID; conversation_type: str; created_by_identity_id: UUID; status: str; created_at: datetime
@dataclass(frozen=True)
class Message:
    id: UUID; channel_id: UUID; sender_identity_id: UUID; content: str; parent_message_id: UUID|None; context_type: str|None; context_id: str|None; status: str; created_at: datetime; edited_at: datetime|None
@dataclass(frozen=True)
class MessageReaction:
    id: UUID; message_id: UUID; identity_id: UUID; reaction: str; created_at: datetime
@dataclass(frozen=True)
class MessageReadState:
    channel_id: UUID; identity_id: UUID; last_read_message_id: UUID|None; updated_at: datetime
