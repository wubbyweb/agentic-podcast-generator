"""Agent communication utilities."""

import json
from typing import Dict, Any, Optional
from datetime import datetime

class AgentCommunication:
    """Handles communication between agents."""

    def __init__(self):
        self.message_queue = []

    def send_message(self, from_agent: str, to_agent: str, action: str, payload: Dict[str, Any]) -> str:
        """Send a message from one agent to another."""
        message = {
            "id": f"msg_{int(datetime.utcnow().timestamp() * 1000)}",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "action": action,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sent"
        }

        self.message_queue.append(message)
        return message["id"]

    def receive_messages(self, agent_name: str) -> list:
        """Receive messages for a specific agent."""
        messages = [
            msg for msg in self.message_queue
            if msg["to_agent"] == agent_name and msg["status"] == "sent"
        ]

        # Mark messages as received
        for msg in messages:
            msg["status"] = "received"

        return messages

    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by its ID."""
        for msg in self.message_queue:
            if msg["id"] == message_id:
                return msg
        return None

    def clear_messages(self, agent_name: Optional[str] = None) -> None:
        """Clear messages from the queue."""
        if agent_name:
            self.message_queue = [
                msg for msg in self.message_queue
                if msg["from_agent"] != agent_name and msg["to_agent"] != agent_name
            ]
        else:
            self.message_queue.clear()

    def get_message_stats(self) -> Dict[str, int]:
        """Get statistics about messages in the queue."""
        total = len(self.message_queue)
        sent = len([msg for msg in self.message_queue if msg["status"] == "sent"])
        received = len([msg for msg in self.message_queue if msg["status"] == "received"])

        return {
            "total": total,
            "sent": sent,
            "received": received,
            "pending": sent
        }