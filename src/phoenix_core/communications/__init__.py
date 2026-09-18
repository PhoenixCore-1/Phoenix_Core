"""Phoenix Core internal communications foundation."""

from .domain import Channel, ChannelMember, Conversation, Message, MessageReaction, MessageReadState
from .service import CommunicationsService

__all__ = [
    "Channel", "ChannelMember", "Conversation", "Message", "MessageReaction",
    "MessageReadState", "CommunicationsService",
]
