"""Async message queue for decoupled channel-agent communication."""

import asyncio

from nanobot.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    Async message bus that decouples chat channels from the agent core.

    Channels push messages to the inbound queue, and the agent processes
    them and pushes responses to the outbound queue.
    
    异步消息总线，将聊天通道与智能体核心解耦。
    通道将消息推入入站队列，智能体处理后通过出站队列推送响应。
    """

    def __init__(self):
        """Initialize the message bus with inbound and outbound queues.
        
        初始化消息总线，创建入站和出站两个异步队列。
        """
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()

    async def publish_inbound(self, msg: InboundMessage) -> None:
        """Publish a message from a channel to the agent.
        
        将消息从通道发布到智能体（入站队列）。
        
        Args:
            msg: 入站消息对象
        """
        await self.inbound.put(msg)

    async def consume_inbound(self) -> InboundMessage:
        """Consume the next inbound message (blocks until available).
        
        消费下一条入站消息（阻塞直到消息可用）。
        
        Returns:
            入站消息对象
        """
        return await self.inbound.get()

    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """Publish a response from the agent to channels.
        
        将智能体的响应发布到通道（出站队列）。
        
        Args:
            msg: 出站消息对象
        """
        await self.outbound.put(msg)

    async def consume_outbound(self) -> OutboundMessage:
        """Consume the next outbound message (blocks until available).
        
        消费下一条出站消息（阻塞直到消息可用）。
        
        Returns:
            出站消息对象
        """
        return await self.outbound.get()

    @property
    def inbound_size(self) -> int:
        """Number of pending inbound messages."""
        return self.inbound.qsize()

    @property
    def outbound_size(self) -> int:
        """Number of pending outbound messages."""
        return self.outbound.qsize()
