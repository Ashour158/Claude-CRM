# omnichannel/email_ingest_minimal.py
"""
Email Ingest Minimal Path Implementation
P2 Priority: 1 inbound ↔ lead association

This module implements:
- Minimal path email ingestion
- Direct email to lead association
- Real-time email processing
- Lead creation and association
- Email content analysis
"""

import logging
import email
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import json

logger = logging.getLogger(__name__)

@dataclass
class EmailMessage:
    """Email message with metadata"""
    id: str
    message_id: str
    from_email: str
    to_email: str
    subject: str
    body: str
    html_body: str
    received_at: timezone.datetime
    company_id: str
    lead_id: Optional[str] = None
    associated_lead: Optional[str] = None
    processed: bool = False

@dataclass
class LeadAssociation:
    """Lead association result"""
    id: str
    email_id: str
    lead_id: str
    association_type: str  # created, matched, updated
    confidence_score: float
    association_reason: str
    created_at: timezone.datetime

@dataclass
class EmailProcessingResult:
    """Email processing result"""
    id: str
    email_id: str
    processing_time_ms: float
    lead_created: bool
    lead_associated: bool
    lead_id: Optional[str]
    confidence_score: float
    processing_errors: List[str]
    created_at: timezone.datetime

class EmailIngestMinimal:
    """
    Minimal path email ingestion with direct lead association
    """
    
    def __init__(self):
        self.email_messages: Dict[str, EmailMessage] = {}
        self.lead_associations: List[LeadAssociation] = []
        self.processing_results: List[EmailProcessingResult] = []
        
        # Email processing configuration
        self.config = {
            "min_confidence_score": 0.7,
            "max_processing_time_ms": 1000,
            "auto_create_leads": True,
            "lead_matching_enabled": True,
            "content_analysis_enabled": True
        }
        
        # Email patterns for lead detection
        self.lead_patterns = {
            "inquiry_keywords": [
                "interested", "inquiry", "question", "information", "quote", "pricing",
                "demo", "trial", "contact", "sales", "buy", "purchase"
            ],
            "contact_keywords": [
                "phone", "call", "speak", "discuss", "meeting", "appointment"
            ],
            "urgency_keywords": [
                "urgent", "asap", "immediately", "soon", "quickly"
            ]
        }
    
    def ingest_email(self, raw_email: str, company: Company) -> EmailMessage:
        """Ingest raw email and create email message"""
        start_time = timezone.now()
        
        try:
            # Parse email
            email_obj = email.message_from_string(raw_email)
            
            # Extract email data
            message_id = email_obj.get('Message-ID', str(uuid.uuid4()))
            from_email = email_obj.get('From', '')
            to_email = email_obj.get('To', '')
            subject = email_obj.get('Subject', '')
            
            # Extract body content
            body, html_body = self._extract_email_body(email_obj)
            
            # Create email message
            email_message = EmailMessage(
                id=str(uuid.uuid4()),
                message_id=message_id,
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                body=body,
                html_body=html_body,
                received_at=timezone.now(),
                company_id=str(company.id)
            )
            
            self.email_messages[email_message.id] = email_message
            
            # Publish email ingestion event
            event_bus.publish(
                event_type='EMAIL_INGESTED',
                data={
                    'email_id': email_message.id,
                    'message_id': message_id,
                    'from_email': from_email,
                    'subject': subject,
                    'company_id': str(company.id)
                },
                company_id=company.id
            )
            
            logger.info(f"Email ingested: {message_id} from {from_email}")
            return email_message
            
        except Exception as e:
            logger.error(f"Email ingestion failed: {e}")
            raise
    
    def _extract_email_body(self, email_obj) -> Tuple[str, str]:
        """Extract text and HTML body from email"""
        body = ""
        html_body = ""
        
        if email_obj.is_multipart():
            for part in email_obj.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            content_type = email_obj.get_content_type()
            if content_type == "text/plain":
                body = email_obj.get_payload(decode=True).decode('utf-8', errors='ignore')
            elif content_type == "text/html":
                html_body = email_obj.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return body, html_body
    
    def process_email_for_lead(self, email_id: str, company: Company) -> EmailProcessingResult:
        """Process email for lead association"""
        if email_id not in self.email_messages:
            raise ValueError(f"Email not found: {email_id}")
        
        email_message = self.email_messages[email_id]
        start_time = time.time()
        
        processing_errors = []
        lead_created = False
        lead_associated = False
        lead_id = None
        confidence_score = 0.0
        
        try:
            # Analyze email content for lead potential
            lead_analysis = self._analyze_email_for_lead(email_message)
            confidence_score = lead_analysis['confidence_score']
            
            if confidence_score >= self.config["min_confidence_score"]:
                # Try to find existing lead
                existing_lead = self._find_existing_lead(email_message, company)
                
                if existing_lead:
                    # Associate with existing lead
                    lead_id = existing_lead
                    lead_associated = True
                    association_type = "matched"
                else:
                    # Create new lead
                    lead_id = self._create_lead_from_email(email_message, company)
                    lead_created = True
                    association_type = "created"
                
                # Create lead association
                association = LeadAssociation(
                    id=str(uuid.uuid4()),
                    email_id=email_id,
                    lead_id=lead_id,
                    association_type=association_type,
                    confidence_score=confidence_score,
                    association_reason=lead_analysis['reason'],
                    created_at=timezone.now()
                )
                
                self.lead_associations.append(association)
                
                # Update email message
                email_message.lead_id = lead_id
                email_message.associated_lead = lead_id
                email_message.processed = True
                
                # Publish lead association event
                event_bus.publish(
                    event_type='EMAIL_LEAD_ASSOCIATED',
                    data={
                        'email_id': email_id,
                        'lead_id': lead_id,
                        'association_type': association_type,
                        'confidence_score': confidence_score
                    },
                    company_id=company.id
                )
                
                logger.info(f"Email {email_id} associated with lead {lead_id} ({association_type})")
            else:
                processing_errors.append(f"Low confidence score: {confidence_score}")
                logger.info(f"Email {email_id} not associated with lead (confidence: {confidence_score})")
        
        except Exception as e:
            processing_errors.append(str(e))
            logger.error(f"Email processing failed for {email_id}: {e}")
        
        # Create processing result
        processing_time = (time.time() - start_time) * 1000
        result = EmailProcessingResult(
            id=str(uuid.uuid4()),
            email_id=email_id,
            processing_time_ms=processing_time,
            lead_created=lead_created,
            lead_associated=lead_associated,
            lead_id=lead_id,
            confidence_score=confidence_score,
            processing_errors=processing_errors,
            created_at=timezone.now()
        )
        
        self.processing_results.append(result)
        
        # Update performance metrics
        self._update_processing_metrics(result)
        
        return result
    
    def _analyze_email_for_lead(self, email_message: EmailMessage) -> Dict[str, Any]:
        """Analyze email content for lead potential"""
        confidence_score = 0.0
        reasons = []
        
        # Check subject for lead indicators
        subject_score = self._analyze_subject(email_message.subject)
        confidence_score += subject_score * 0.3
        if subject_score > 0.5:
            reasons.append("Subject indicates lead interest")
        
        # Check body content for lead indicators
        body_score = self._analyze_body(email_message.body)
        confidence_score += body_score * 0.4
        if body_score > 0.5:
            reasons.append("Body content indicates lead interest")
        
        # Check sender domain
        domain_score = self._analyze_sender_domain(email_message.from_email)
        confidence_score += domain_score * 0.2
        if domain_score > 0.5:
            reasons.append("Sender domain indicates business interest")
        
        # Check for contact information
        contact_score = self._analyze_contact_info(email_message.body)
        confidence_score += contact_score * 0.1
        if contact_score > 0.5:
            reasons.append("Contains contact information")
        
        return {
            'confidence_score': min(1.0, confidence_score),
            'reason': '; '.join(reasons) if reasons else 'No clear lead indicators'
        }
    
    def _analyze_subject(self, subject: str) -> float:
        """Analyze email subject for lead indicators"""
        if not subject:
            return 0.0
        
        subject_lower = subject.lower()
        score = 0.0
        
        # Check for inquiry keywords
        for keyword in self.lead_patterns["inquiry_keywords"]:
            if keyword in subject_lower:
                score += 0.2
        
        # Check for contact keywords
        for keyword in self.lead_patterns["contact_keywords"]:
            if keyword in subject_lower:
                score += 0.15
        
        # Check for urgency keywords
        for keyword in self.lead_patterns["urgency_keywords"]:
            if keyword in subject_lower:
                score += 0.1
        
        return min(1.0, score)
    
    def _analyze_body(self, body: str) -> float:
        """Analyze email body for lead indicators"""
        if not body:
            return 0.0
        
        body_lower = body.lower()
        score = 0.0
        
        # Check for inquiry keywords
        for keyword in self.lead_patterns["inquiry_keywords"]:
            if keyword in body_lower:
                score += 0.1
        
        # Check for contact keywords
        for keyword in self.lead_patterns["contact_keywords"]:
            if keyword in body_lower:
                score += 0.1
        
        # Check for urgency keywords
        for keyword in self.lead_patterns["urgency_keywords"]:
            if keyword in body_lower:
                score += 0.05
        
        # Check for question marks (indicates inquiry)
        question_count = body_lower.count('?')
        score += min(0.2, question_count * 0.05)
        
        return min(1.0, score)
    
    def _analyze_sender_domain(self, from_email: str) -> float:
        """Analyze sender domain for business indicators"""
        if not from_email:
            return 0.0
        
        # Extract domain
        domain = from_email.split('@')[-1].lower() if '@' in from_email else ''
        
        # Check for business domains
        business_indicators = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        if domain in business_indicators:
            return 0.3  # Personal email, lower confidence
        
        # Check for company domains
        if '.' in domain and len(domain) > 5:
            return 0.7  # Company domain, higher confidence
        
        return 0.5  # Unknown domain
    
    def _analyze_contact_info(self, body: str) -> float:
        """Analyze body for contact information"""
        if not body:
            return 0.0
        
        score = 0.0
        
        # Check for phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, body):
            score += 0.3
        
        # Check for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, body):
            score += 0.2
        
        # Check for website URLs
        url_pattern = r'https?://[^\s]+'
        if re.search(url_pattern, body):
            score += 0.2
        
        return min(1.0, score)
    
    def _find_existing_lead(self, email_message: EmailMessage, company: Company) -> Optional[str]:
        """Find existing lead by email address"""
        # In a real implementation, this would query the database
        # For now, return None to always create new leads
        return None
    
    def _create_lead_from_email(self, email_message: EmailMessage, company: Company) -> str:
        """Create new lead from email message"""
        # Extract lead information from email
        lead_data = {
            'email': email_message.from_email,
            'first_name': self._extract_first_name(email_message.from_email),
            'last_name': self._extract_last_name(email_message.from_email),
            'company': self._extract_company_from_email(email_message.from_email),
            'source': 'Email',
            'status': 'New',
            'subject': email_message.subject,
            'notes': f"Initial contact via email: {email_message.subject}"
        }
        
        # In a real implementation, this would create a lead in the database
        # For now, generate a mock lead ID
        lead_id = str(uuid.uuid4())
        
        # Publish lead creation event
        event_bus.publish(
            event_type='LEAD_CREATED_FROM_EMAIL',
            data={
                'lead_id': lead_id,
                'email_id': email_message.id,
                'lead_data': lead_data
            },
            company_id=company.id
        )
        
        logger.info(f"Lead created from email: {lead_id}")
        return lead_id
    
    def _extract_first_name(self, email: str) -> str:
        """Extract first name from email address"""
        if '@' in email:
            name_part = email.split('@')[0]
            if '.' in name_part:
                return name_part.split('.')[0].title()
            return name_part.title()
        return ""
    
    def _extract_last_name(self, email: str) -> str:
        """Extract last name from email address"""
        if '@' in email:
            name_part = email.split('@')[0]
            if '.' in name_part:
                return name_part.split('.')[1].title()
        return ""
    
    def _extract_company_from_email(self, email: str) -> str:
        """Extract company from email domain"""
        if '@' in email:
            domain = email.split('@')[1]
            # Remove common email providers
            if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
                return domain.split('.')[0].title()
        return ""
    
    def _update_processing_metrics(self, result: EmailProcessingResult):
        """Update processing metrics"""
        # This would typically update a metrics store
        logger.info(f"Email processing metrics: {result.processing_time_ms:.2f}ms, "
                   f"lead_created: {result.lead_created}, confidence: {result.confidence_score}")
    
    def get_ingestion_metrics(self, company: Company, 
                             lookback_hours: int = 24) -> Dict[str, Any]:
        """Get email ingestion metrics"""
        cutoff_time = timezone.now() - timedelta(hours=lookback_hours)
        
        # Filter data by company and time
        company_emails = [
            email for email in self.email_messages.values()
            if email.company_id == str(company.id) and email.received_at >= cutoff_time
        ]
        
        company_results = [
            result for result in self.processing_results
            if result.created_at >= cutoff_time
        ]
        
        if not company_emails:
            return {"status": "no_data", "message": "No email data available"}
        
        # Calculate metrics
        total_emails = len(company_emails)
        processed_emails = len([e for e in company_emails if e.processed])
        leads_created = len([r for r in company_results if r.lead_created])
        leads_associated = len([r for r in company_results if r.lead_associated])
        
        # Calculate success rate
        success_rate = (leads_created + leads_associated) / total_emails if total_emails > 0 else 0
        
        # Calculate average processing time
        avg_processing_time = np.mean([r.processing_time_ms for r in company_results]) if company_results else 0
        
        # Calculate average confidence score
        avg_confidence = np.mean([r.confidence_score for r in company_results]) if company_results else 0
        
        return {
            "company_id": str(company.id),
            "period_hours": lookback_hours,
            "total_emails": total_emails,
            "processed_emails": processed_emails,
            "leads_created": leads_created,
            "leads_associated": leads_associated,
            "success_rate": success_rate,
            "avg_processing_time_ms": avg_processing_time,
            "avg_confidence_score": avg_confidence,
            "target_met": success_rate >= 0.8,  # 80% success rate target
            "processing_rate": processed_emails / total_emails if total_emails > 0 else 0
        }
    
    def get_lead_associations(self, company: Company, 
                             lookback_hours: int = 24) -> List[Dict[str, Any]]:
        """Get lead associations for a company"""
        cutoff_time = timezone.now() - timedelta(hours=lookback_hours)
        
        company_associations = [
            assoc for assoc in self.lead_associations
            if assoc.created_at >= cutoff_time
        ]
        
        return [
            {
                "id": assoc.id,
                "email_id": assoc.email_id,
                "lead_id": assoc.lead_id,
                "association_type": assoc.association_type,
                "confidence_score": assoc.confidence_score,
                "reason": assoc.association_reason,
                "created_at": assoc.created_at.isoformat()
            }
            for assoc in company_associations
        ]

# Global instance
email_ingest_minimal = EmailIngestMinimal()
