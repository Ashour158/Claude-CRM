# omnichannel/ingestion.py
# Omnichannel Communication Ingestion Engine

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import requests
from celery import shared_task

from .models import (
    CommunicationChannel, Conversation, Message, ConversationTemplate,
    ConversationRule, ConversationMetric, ConversationAnalytics
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class OmnichannelIngestionEngine:
    """
    Advanced omnichannel communication ingestion engine
    that handles multiple communication channels and formats.
    """
    
    def __init__(self):
        self.channel_processors = {
            'email': self._process_email,
            'phone': self._process_phone,
            'sms': self._process_sms,
            'chat': self._process_chat,
            'social_media': self._process_social_media,
            'web_form': self._process_web_form,
            'whatsapp': self._process_whatsapp,
            'telegram': self._process_telegram,
            'slack': self._process_slack,
            'teams': self._process_teams,
        }
    
    def ingest_message(self, channel_id: str, raw_data: Dict[str, Any]) -> Optional[Conversation]:
        """
        Ingest a message from any communication channel.
        """
        try:
            channel = CommunicationChannel.objects.get(id=channel_id)
            
            # Process based on channel type
            processor = self.channel_processors.get(channel.channel_type)
            if not processor:
                logger.error(f"No processor found for channel type: {channel.channel_type}")
                return None
            
            # Process the message
            conversation = processor(channel, raw_data)
            
            # Apply automation rules
            self._apply_automation_rules(conversation)
            
            # Update channel statistics
            self._update_channel_stats(channel)
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to ingest message: {str(e)}")
            return None
    
    def _process_email(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process email messages"""
        # Extract email data
        subject = data.get('subject', '')
        body = data.get('body', '')
        from_email = data.get('from', '')
        to_email = data.get('to', '')
        thread_id = data.get('thread_id', '')
        
        # Find or create customer
        customer = self._find_or_create_customer(from_email, data.get('customer_data', {}))
        
        # Find existing conversation by thread_id
        conversation = None
        if thread_id:
            conversation = Conversation.objects.filter(
                company=channel.company,
                external_id=thread_id
            ).first()
        
        # Create new conversation if not found
        if not conversation:
            conversation = Conversation.objects.create(
                company=channel.company,
                channel=channel,
                subject=subject,
                description=body[:500],
                customer=customer,
                external_id=thread_id,
                status='new',
                priority='medium'
            )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=body,
            content_type='text/html',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound',
            external_id=data.get('message_id', ''),
            thread_id=thread_id
        )
        
        return conversation
    
    def _process_phone(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process phone calls"""
        phone_number = data.get('phone_number', '')
        call_duration = data.get('duration', 0)
        call_type = data.get('call_type', 'inbound')
        recording_url = data.get('recording_url', '')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_phone(phone_number, data.get('customer_data', {}))
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"Phone Call - {phone_number}",
            description=f"Call duration: {call_duration} seconds",
            customer=customer,
            status='new',
            priority='high' if call_type == 'inbound' else 'medium'
        )
        
        # Create message with call details
        Message.objects.create(
            conversation=conversation,
            content=f"Phone call from {phone_number}. Duration: {call_duration}s",
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound',
            attachments=[{'type': 'recording', 'url': recording_url}] if recording_url else []
        )
        
        return conversation
    
    def _process_sms(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process SMS messages"""
        phone_number = data.get('phone_number', '')
        message_text = data.get('message', '')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_phone(phone_number, data.get('customer_data', {}))
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"SMS from {phone_number}",
            description=message_text,
            customer=customer,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound'
        )
        
        return conversation
    
    def _process_chat(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process live chat messages"""
        visitor_id = data.get('visitor_id', '')
        message_text = data.get('message', '')
        visitor_name = data.get('visitor_name', 'Anonymous')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_visitor_id(visitor_id, {
            'name': visitor_name,
            'email': data.get('visitor_email', ''),
            'phone': data.get('visitor_phone', '')
        })
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"Live Chat - {visitor_name}",
            description=message_text,
            customer=customer,
            external_id=visitor_id,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound'
        )
        
        return conversation
    
    def _process_social_media(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process social media messages"""
        platform = data.get('platform', '')
        post_id = data.get('post_id', '')
        message_text = data.get('message', '')
        author = data.get('author', {})
        
        # Find or create customer
        customer = self._find_or_create_customer_by_social_id(
            author.get('id', ''),
            {
                'name': author.get('name', ''),
                'username': author.get('username', ''),
                'email': author.get('email', ''),
                'platform': platform
            }
        )
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"{platform.title()} - {author.get('name', 'Unknown')}",
            description=message_text,
            customer=customer,
            external_id=post_id,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound',
            metadata={'platform': platform, 'post_id': post_id}
        )
        
        return conversation
    
    def _process_web_form(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process web form submissions"""
        form_data = data.get('form_data', {})
        form_name = data.get('form_name', 'Contact Form')
        
        # Find or create customer
        customer = self._find_or_create_customer(
            form_data.get('email', ''),
            {
                'name': form_data.get('name', ''),
                'phone': form_data.get('phone', ''),
                'company': form_data.get('company', '')
            }
        )
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"Web Form - {form_name}",
            description=form_data.get('message', ''),
            customer=customer,
            status='new',
            priority='medium'
        )
        
        # Create message with form data
        Message.objects.create(
            conversation=conversation,
            content=f"Form submission: {json.dumps(form_data, indent=2)}",
            content_type='application/json',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound'
        )
        
        return conversation
    
    def _process_whatsapp(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process WhatsApp messages"""
        phone_number = data.get('phone_number', '')
        message_text = data.get('message', '')
        message_type = data.get('message_type', 'text')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_phone(phone_number, data.get('customer_data', {}))
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"WhatsApp - {phone_number}",
            description=message_text,
            customer=customer,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type=f'text/{message_type}',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound',
            metadata={'whatsapp_type': message_type}
        )
        
        return conversation
    
    def _process_telegram(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process Telegram messages"""
        user_id = data.get('user_id', '')
        message_text = data.get('message', '')
        username = data.get('username', '')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_telegram_id(user_id, {
            'username': username,
            'name': data.get('first_name', ''),
            'last_name': data.get('last_name', '')
        })
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"Telegram - @{username}",
            description=message_text,
            customer=customer,
            external_id=user_id,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound'
        )
        
        return conversation
    
    def _process_slack(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process Slack messages"""
        user_id = data.get('user_id', '')
        message_text = data.get('message', '')
        channel_name = data.get('channel_name', '')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_slack_id(user_id, {
            'name': data.get('user_name', ''),
            'email': data.get('user_email', '')
        })
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"Slack - #{channel_name}",
            description=message_text,
            customer=customer,
            external_id=user_id,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound'
        )
        
        return conversation
    
    def _process_teams(self, channel: CommunicationChannel, data: Dict[str, Any]) -> Conversation:
        """Process Microsoft Teams messages"""
        user_id = data.get('user_id', '')
        message_text = data.get('message', '')
        team_name = data.get('team_name', '')
        
        # Find or create customer
        customer = self._find_or_create_customer_by_teams_id(user_id, {
            'name': data.get('user_name', ''),
            'email': data.get('user_email', '')
        })
        
        # Create conversation
        conversation = Conversation.objects.create(
            company=channel.company,
            channel=channel,
            subject=f"Teams - {team_name}",
            description=message_text,
            customer=customer,
            external_id=user_id,
            status='new',
            priority='medium'
        )
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            content=message_text,
            content_type='text/plain',
            sender=customer,
            recipient=User.objects.filter(company=channel.company).first(),
            direction='incoming',
            message_type='inbound'
        )
        
        return conversation
    
    def _find_or_create_customer(self, email: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by email"""
        if not email:
            # Create anonymous customer
            return User.objects.create(
                company=Company.objects.first(),  # Default company
                email=f"anonymous_{timezone.now().timestamp()}@example.com",
                first_name=customer_data.get('name', 'Anonymous'),
                is_active=False
            )
        
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=email,
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                phone=customer_data.get('phone', ''),
                is_active=True
            )
    
    def _find_or_create_customer_by_phone(self, phone: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by phone number"""
        if not phone:
            return self._find_or_create_customer('', customer_data)
        
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=customer_data.get('email', f"{phone}@example.com"),
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                phone=phone,
                is_active=True
            )
    
    def _find_or_create_customer_by_visitor_id(self, visitor_id: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by visitor ID"""
        if not visitor_id:
            return self._find_or_create_customer('', customer_data)
        
        # Try to find by visitor ID in metadata
        try:
            return User.objects.get(metadata__visitor_id=visitor_id)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=customer_data.get('email', f"visitor_{visitor_id}@example.com"),
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                phone=customer_data.get('phone', ''),
                metadata={'visitor_id': visitor_id},
                is_active=True
            )
    
    def _find_or_create_customer_by_social_id(self, social_id: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by social media ID"""
        if not social_id:
            return self._find_or_create_customer('', customer_data)
        
        try:
            return User.objects.get(metadata__social_id=social_id)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=customer_data.get('email', f"social_{social_id}@example.com"),
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                username=customer_data.get('username', ''),
                metadata={'social_id': social_id, 'platform': customer_data.get('platform', '')},
                is_active=True
            )
    
    def _find_or_create_customer_by_telegram_id(self, telegram_id: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by Telegram ID"""
        if not telegram_id:
            return self._find_or_create_customer('', customer_data)
        
        try:
            return User.objects.get(metadata__telegram_id=telegram_id)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=f"telegram_{telegram_id}@example.com",
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                username=customer_data.get('username', ''),
                metadata={'telegram_id': telegram_id},
                is_active=True
            )
    
    def _find_or_create_customer_by_slack_id(self, slack_id: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by Slack ID"""
        if not slack_id:
            return self._find_or_create_customer('', customer_data)
        
        try:
            return User.objects.get(metadata__slack_id=slack_id)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=customer_data.get('email', f"slack_{slack_id}@example.com"),
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                metadata={'slack_id': slack_id},
                is_active=True
            )
    
    def _find_or_create_customer_by_teams_id(self, teams_id: str, customer_data: Dict[str, Any]) -> User:
        """Find or create customer by Teams ID"""
        if not teams_id:
            return self._find_or_create_customer('', customer_data)
        
        try:
            return User.objects.get(metadata__teams_id=teams_id)
        except User.DoesNotExist:
            return User.objects.create(
                company=Company.objects.first(),
                email=customer_data.get('email', f"teams_{teams_id}@example.com"),
                first_name=customer_data.get('name', ''),
                last_name=customer_data.get('last_name', ''),
                metadata={'teams_id': teams_id},
                is_active=True
            )
    
    def _apply_automation_rules(self, conversation: Conversation):
        """Apply automation rules to conversation"""
        rules = ConversationRule.objects.filter(
            company=conversation.company,
            channels=conversation.channel,
            is_active=True
        ).order_by('priority')
        
        for rule in rules:
            if self._evaluate_rule_conditions(rule, conversation):
                self._execute_rule_actions(rule, conversation)
    
    def _evaluate_rule_conditions(self, rule: ConversationRule, conversation: Conversation) -> bool:
        """Evaluate if rule conditions are met"""
        conditions = rule.conditions
        
        # Check channel type
        if 'channel_type' in conditions:
            if conversation.channel.channel_type != conditions['channel_type']:
                return False
        
        # Check priority
        if 'priority' in conditions:
            if conversation.priority != conditions['priority']:
                return False
        
        # Check keywords
        if 'keywords' in conditions:
            keywords = conditions['keywords']
            subject_match = any(keyword.lower() in conversation.subject.lower() for keyword in keywords)
            if not subject_match:
                return False
        
        # Check customer type
        if 'customer_type' in conditions:
            # This would require additional customer classification logic
            pass
        
        return True
    
    def _execute_rule_actions(self, rule: ConversationRule, conversation: Conversation):
        """Execute rule actions"""
        actions = rule.actions
        
        # Auto-assign
        if 'auto_assign' in actions:
            assigned_user_id = actions['auto_assign'].get('user_id')
            if assigned_user_id:
                try:
                    user = User.objects.get(id=assigned_user_id, company=conversation.company)
                    conversation.assigned_agent = user
                    conversation.status = 'open'
                    conversation.save()
                except User.DoesNotExist:
                    pass
        
        # Auto-reply
        if 'auto_reply' in actions:
            template_id = actions['auto_reply'].get('template_id')
            if template_id:
                try:
                    template = ConversationTemplate.objects.get(id=template_id)
                    # Send auto-reply message
                    Message.objects.create(
                        conversation=conversation,
                        content=template.content_template,
                        content_type='text/plain',
                        sender=User.objects.filter(company=conversation.company).first(),
                        recipient=conversation.customer,
                        direction='outgoing',
                        message_type='auto_reply'
                    )
                except ConversationTemplate.DoesNotExist:
                    pass
        
        # Set priority
        if 'set_priority' in actions:
            conversation.priority = actions['set_priority']
            conversation.save()
        
        # Add tags
        if 'add_tags' in actions:
            tags = actions['add_tags']
            conversation.tags.extend(tags)
            conversation.save()
        
        # Update rule statistics
        rule.execution_count += 1
        rule.success_count += 1
        rule.last_executed = timezone.now()
        rule.save()
    
    def _update_channel_stats(self, channel: CommunicationChannel):
        """Update channel statistics"""
        channel.total_conversations = Conversation.objects.filter(
            company=channel.company,
            channel=channel
        ).count()
        
        channel.active_conversations = Conversation.objects.filter(
            company=channel.company,
            channel=channel,
            status__in=['new', 'open', 'pending']
        ).count()
        
        # Calculate average response time
        conversations_with_response_time = Conversation.objects.filter(
            company=channel.company,
            channel=channel,
            first_response_time__isnull=False
        )
        
        if conversations_with_response_time.exists():
            avg_response_time = conversations_with_response_time.aggregate(
                avg_time=models.Avg('first_response_time')
            )['avg_time']
            channel.average_response_time = avg_response_time or 0
        
        channel.save()

# Celery tasks for async processing
@shared_task
def process_ingested_message(channel_id: str, raw_data: Dict[str, Any]):
    """Celery task to process ingested messages asynchronously"""
    engine = OmnichannelIngestionEngine()
    return engine.ingest_message(channel_id, raw_data)

@shared_task
def sync_channel_data(channel_id: str):
    """Celery task to sync data from external channels"""
    try:
        channel = CommunicationChannel.objects.get(id=channel_id)
        
        # This would integrate with external APIs
        # For now, it's a placeholder
        logger.info(f"Syncing data for channel: {channel.name}")
        
    except CommunicationChannel.DoesNotExist:
        logger.error(f"Channel not found: {channel_id}")
    except Exception as e:
        logger.error(f"Failed to sync channel data: {str(e)}")
