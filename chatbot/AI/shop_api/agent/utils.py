import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def clean_ai_response(response_text: str) -> str:
    """Clean AI response by removing artifacts and formatting issues."""
    if not response_text:
        return ""

    # Remove special tokens and artifacts
    artifacts_to_remove = [
        r'^<s>', r'</s>$',
        r'^\[INST\]', r'\[/INST\]$',
        r'^s>\s*', r'^S>\s*',
        r'^</s>\s*', r'<s>\s*$',
        r'<[^>]+>',
        r'```.*?```',
        r'^(Assistant|AI|Bot):\s*',
        r'^(Response|Answer):\s*',
        r'^\d+\.\s+',
        r'^\([^)]+\)\s*',
        r'^\[[^\]]+\]\s*',
    ]

    for pattern in artifacts_to_remove:
        response_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)

    # Remove unwanted conversational prefixes
    unwanted_prefixes = [
        'Sure!', 'Okay!', 'Alright!', 'Hello!', 'Hi!',
        'Great question!', 'Thanks for asking!',
        'I understand.', 'Let me help.', 'I can help with that.'
    ]

    for prefix in unwanted_prefixes:
        if response_text.lower().startswith(prefix.lower()):
            response_text = response_text[len(prefix):].lstrip()

    # Clean up whitespace
    response_text = re.sub(r'\n\s*\n+', '\n\n', response_text)
    lines = [line.strip() for line in response_text.split('\n')]
    response_text = '\n'.join(lines)
    response_text = re.sub(r'\s{3,}', '  ', response_text)

    # Ensure proper sentence structure
    if response_text and response_text[-1] not in ['.', '!', '?', ':', ';']:
        response_text += '.'
    if response_text and response_text[0].islower():
        response_text = response_text[0].upper() + response_text[1:]

    # Remove remaining artifacts
    response_text = re.sub(r'\[|\]', '', response_text)
    response_text = re.sub(r'<|>', '', response_text)
    response_text = re.sub(r'\*+', '', response_text)
    response_text = response_text.replace('`', '')

    # Final cleanup
    response_text = response_text.strip()
    response_text = re.sub(r'([.!?])\1+', r'\1', response_text)

    # Remove very short responses
    sentences = response_text.split('. ')
    valid_sentences = []
    for sentence in sentences:
        clean_sentence = re.sub(r'[^\w\s]', '', sentence).strip()
        if len(clean_sentence) > 3:
            valid_sentences.append(sentence)
    response_text = '. '.join(valid_sentences)

    if not response_text or len(response_text) < 3:
        return "I understand. How else can I assist you today?"

    return response_text


def format_operating_hours(operating_hours: Dict[str, str]) -> str:
    """Format operating hours for display."""
    if not operating_hours:
        return "Please contact for hours"
    
    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    formatted = []
    
    for day in days_order:
        if day in operating_hours:
            hours = operating_hours[day]
            day_name = day.capitalize()
            formatted.append(f"{day_name}: {hours}")
    
    return "\n".join(formatted)


def format_services(services: list) -> str:
    """Format services list for display."""
    if not services:
        return "No services listed"
    
    formatted = []
    for service in services:
        name = service.get('name', 'Unknown Service')
        price = f"${service.get('price', 0):.2f}"
        duration = service.get('duration_minutes', '')
        
        line = f"- {name} - {price}"
        if duration:
            line += f" ({duration} minutes)"
            
        formatted.append(line)
    
    return "\n".join(formatted)


def extract_reservation_id(message: str) -> Optional[str]:
    """Extract reservation ID from message."""
    match = re.search(r'RES\d+', message.upper())
    return match.group(0) if match else None


def extract_phone_number(message: str) -> Optional[str]:
    """Extract phone number from message."""
    phone_patterns = [
        r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\d{10}\b',
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, message)
        if match:
            phone = match.group(0)
            phone = re.sub(r'[^\d+]', '', phone)
            return phone
    return None


def extract_email(message: str) -> Optional[str]:
    """Extract email from message."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, message)
    return match.group(0) if match else None


def format_user_context(session_data: Dict[str, Any]) -> str:
    """Format user context for AI prompt."""
    if not session_data:
        return "No customer information available yet."
    
    context = []
    if session_data.get('user_name'):
        context.append(f"Name: {session_data.get('user_name')}")
    if session_data.get('user_email'):
        context.append(f"Email: {session_data.get('user_email')}")
    if session_data.get('user_phone'):
        context.append(f"Phone: {session_data.get('user_phone')}")
    
    return "\n".join(context) if context else "No customer information available yet."