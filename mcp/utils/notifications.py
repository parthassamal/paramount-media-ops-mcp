"""
Notification system for pipeline events.

Supports:
- Slack webhooks
- Jira comments
- Email (via SMTP)

Events:
- REVIEW_PENDING: Test cases ready for review
- SLA_BREACH: Review exceeded 24h SLA
- PIPELINE_FAILED: Pipeline failed at a stage
- PIPELINE_STALLED: No progress for 30+ minutes during active incident
- VERIFICATION_COMPLETE: TestRail verification run finished
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class NotificationChannel:
    """Base class for notification channels."""
    
    async def send(self, event_type: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError


class SlackNotifier(NotificationChannel):
    """Slack webhook notifier."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
        self.enabled = bool(self.webhook_url)
    
    async def send(self, event_type: str, data: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        
        message = self._format_message(event_type, data)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                logger.info("slack_notification_sent", event=event_type)
                return True
        except Exception as e:
            logger.error("slack_notification_failed", event=event_type, error=str(e))
            return False
    
    def _format_message(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format notification as Slack block message."""
        
        templates = {
            "review_pending": {
                "emoji": ":clipboard:",
                "color": "#FFA500",
                "title": "Test Cases Ready for Review",
                "fields": [
                    ("RCA ID", data.get("rca_id", "N/A")),
                    ("Jira Ticket", data.get("jira_ticket_id", "N/A")),
                    ("Test Cases", str(data.get("cases_count", 0))),
                    ("SLA Deadline", data.get("sla_deadline", "24 hours"))
                ]
            },
            "sla_breach": {
                "emoji": ":warning:",
                "color": "#FF0000",
                "title": "SLA BREACH - Review Overdue",
                "fields": [
                    ("RCA ID", data.get("rca_id", "N/A")),
                    ("Jira Ticket", data.get("jira_ticket_id", "N/A")),
                    ("Hours Overdue", f"{data.get('hours_overdue', 0):.1f}h")
                ]
            },
            "pipeline_failed": {
                "emoji": ":x:",
                "color": "#FF0000",
                "title": "Pipeline Failed",
                "fields": [
                    ("RCA ID", data.get("rca_id", "N/A")),
                    ("Failed Stage", data.get("stage", "N/A")),
                    ("Error", data.get("error", "Unknown")[:200])
                ]
            },
            "pipeline_stalled": {
                "emoji": ":hourglass:",
                "color": "#FFA500",
                "title": "Pipeline Stalled - No Progress",
                "fields": [
                    ("RCA ID", data.get("rca_id", "N/A")),
                    ("Current Stage", data.get("stage", "N/A")),
                    ("Stalled For", f"{data.get('stalled_for_minutes', 0):.0f} minutes")
                ]
            },
            "verification_complete": {
                "emoji": ":white_check_mark:",
                "color": "#00FF00",
                "title": "Verification Run Complete",
                "fields": [
                    ("RCA ID", data.get("rca_id", "N/A")),
                    ("Passed", str(data.get("passed", 0))),
                    ("Failed", str(data.get("failed", 0)))
                ]
            }
        }
        
        template = templates.get(event_type, {
            "emoji": ":bell:",
            "color": "#808080",
            "title": event_type.replace("_", " ").title(),
            "fields": [(k, str(v)) for k, v in data.items()]
        })
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{template['emoji']} {template['title']}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*{name}:*\n{value}"}
                    for name, value in template["fields"]
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Paramount+ RCA Pipeline • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                    }
                ]
            }
        ]
        
        return {
            "blocks": blocks,
            "attachments": [{"color": template["color"]}]
        }


class JiraCommentNotifier(NotificationChannel):
    """Add comments to Jira tickets for pipeline events."""
    
    def __init__(self):
        from config import settings
        self.jira_url = settings.jira_api_url.rstrip("/")
        self.jira_email = settings.jira_api_email
        self.jira_token = settings.jira_api_token
        self.enabled = bool(self.jira_url and self.jira_email and self.jira_token)
    
    async def send(self, event_type: str, data: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        
        jira_key = data.get("jira_ticket_id")
        if not jira_key:
            return False
        
        comment = self._format_comment(event_type, data)
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.jira_url}/rest/api/3/issue/{jira_key}/comment",
                    auth=(self.jira_email, self.jira_token),
                    headers={"Content-Type": "application/json"},
                    json={
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": comment}]
                                }
                            ]
                        }
                    }
                )
                response.raise_for_status()
                logger.info("jira_comment_added", event=event_type, jira=jira_key)
                return True
        except Exception as e:
            logger.error("jira_comment_failed", event=event_type, jira=jira_key, error=str(e))
            return False
    
    def _format_comment(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format notification as Jira comment."""
        
        templates = {
            "review_pending": (
                f"🔔 *RCA Pipeline - Test Cases Ready for Review*\n\n"
                f"RCA ID: {data.get('rca_id', 'N/A')}\n"
                f"Generated Test Cases: {data.get('cases_count', 0)}\n"
                f"Match Confidence: {data.get('match_confidence', 'N/A')}\n\n"
                f"SLA: 24 hours for human review\n"
                f"Review URL: /api/rca/review/pending"
            ),
            "pipeline_failed": (
                f"❌ *RCA Pipeline Failed*\n\n"
                f"RCA ID: {data.get('rca_id', 'N/A')}\n"
                f"Failed at: {data.get('stage', 'N/A')}\n"
                f"Error: {data.get('error', 'Unknown')}\n\n"
                f"Action required: Resume pipeline or investigate manually"
            ),
            "verification_complete": (
                f"✅ *Verification Run Complete*\n\n"
                f"RCA ID: {data.get('rca_id', 'N/A')}\n"
                f"Passed: {data.get('passed', 0)}\n"
                f"Failed: {data.get('failed', 0)}\n"
                f"Run ID: {data.get('run_id', 'N/A')}"
            )
        }
        
        return templates.get(event_type, f"RCA Pipeline Event: {event_type}\n\n{json.dumps(data, indent=2)}")


class NotificationManager:
    """
    Manages multiple notification channels.
    
    Usage:
        notifier = NotificationManager()
        await notifier.notify("review_pending", {"rca_id": "...", "jira_ticket_id": "PROD-123"})
    """
    
    _instance: Optional["NotificationManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._channels: List[NotificationChannel] = []
        self._setup_channels()
        self._initialized = True
    
    def _setup_channels(self):
        """Initialize enabled notification channels."""
        
        # Slack
        slack = SlackNotifier()
        if slack.enabled:
            self._channels.append(slack)
            logger.info("notification_channel_enabled", channel="slack")
        
        # Jira comments
        jira = JiraCommentNotifier()
        if jira.enabled:
            self._channels.append(jira)
            logger.info("notification_channel_enabled", channel="jira")
    
    async def notify(self, event_type: str, data: Dict[str, Any]) -> int:
        """
        Send notification to all enabled channels.
        
        Args:
            event_type: Type of event (review_pending, sla_breach, etc.)
            data: Event data dictionary
            
        Returns:
            Number of channels that successfully sent the notification
        """
        success_count = 0
        
        for channel in self._channels:
            try:
                if await channel.send(event_type, data):
                    success_count += 1
            except Exception as e:
                logger.error(
                    "notification_channel_error",
                    channel=type(channel).__name__,
                    event=event_type,
                    error=str(e)
                )
        
        logger.info(
            "notifications_sent",
            event=event_type,
            channels_total=len(self._channels),
            channels_success=success_count
        )
        
        return success_count
    
    def add_channel(self, channel: NotificationChannel):
        """Add a custom notification channel."""
        self._channels.append(channel)


# Global singleton
notifier = NotificationManager()


async def notify(event_type: str, data: Dict[str, Any]) -> int:
    """Convenience function to send a notification."""
    return await notifier.notify(event_type, data)
