#!/usr/bin/env python3
"""
Comprehensive timeline extraction and parsing system
Handles natural language time expressions and converts them to specific datetime objects
"""

import re
from datetime import datetime, timedelta, time
from typing import Optional, Tuple, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimelineExtractor:
    """
    Extracts and parses natural language timeline expressions
    """
    
    def __init__(self):
        self.now = datetime.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        
        # Time patterns for specific times
        self.time_patterns = [
            # 12:00, 12:00pm, 12:00 AM, 12:00PM
            r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?',
            # 12pm, 12am, 12 PM, 12 AM
            r'(\d{1,2})\s*(am|pm|AM|PM)',
            # noon, midnight
            r'(noon|midnight)',
            # morning, afternoon, evening, night
            r'(morning|afternoon|evening|night)',
        ]
        
        # Timeline patterns with priorities (higher number = higher priority)
        self.timeline_patterns = [
            # Specific times (highest priority)
            (r'at\s+(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?', 100, 'specific_time'),
            (r'at\s+(\d{1,2})\s*(am|pm|AM|PM)', 100, 'specific_time'),
            (r'at\s+(noon|midnight)', 100, 'specific_time'),
            (r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?', 95, 'specific_time'),
            (r'(\d{1,2})\s*(am|pm|AM|PM)', 95, 'specific_time'),
            
            # Relative times with specific periods
            (r'in\s+(\d+)\s+hours?', 90, 'hours'),
            (r'in\s+(\d+)\s+minutes?', 90, 'minutes'),
            (r'in\s+(\d+)\s+days?', 80, 'days'),
            (r'in\s+(\d+)\s+weeks?', 80, 'weeks'),
            (r'in\s+(\d+)\s+months?', 80, 'months'),
            
            # Natural language expressions
            (r'next\s+week', 70, 'next_week'),
            (r'next\s+month', 70, 'next_month'),
            (r'next\s+year', 70, 'next_year'),
            (r'tomorrow', 60, 'tomorrow'),
            (r'today', 60, 'today'),
            (r'this\s+week', 60, 'this_week'),
            (r'this\s+month', 60, 'this_month'),
            (r'this\s+year', 60, 'this_year'),
            
            # Vague expressions
            (r'in\s+a\s+few\s+hours?', 50, 'few_hours'),
            (r'in\s+a\s+couple\s+hours?', 50, 'few_hours'),
            (r'in\s+a\s+few\s+days?', 50, 'few_days'),
            (r'in\s+a\s+couple\s+days?', 50, 'few_days'),
            (r'in\s+a\s+few\s+weeks?', 50, 'few_weeks'),
            (r'in\s+a\s+couple\s+weeks?', 50, 'few_weeks'),
            (r'in\s+a\s+few\s+months?', 50, 'few_months'),
            (r'in\s+a\s+couple\s+months?', 50, 'few_months'),
            (r'later', 40, 'later'),
            (r'soon', 40, 'soon'),
        ]
    
    def extract_timeline(self, message: str) -> Dict[str, Any]:
        """
        Extract timeline information from a message
        
        Returns:
            Dict with 'timeline_text', 'datetime', 'confidence', 'type'
        """
        message_lower = message.lower().strip()
        
        # Find the best matching pattern
        best_match = None
        best_priority = -1
        
        for pattern, priority, pattern_type in self.timeline_patterns:
            match = re.search(pattern, message_lower)
            if match and priority > best_priority:
                best_match = (match, pattern_type, priority)
                best_priority = priority
        
        if best_match:
            match, pattern_type, priority = best_match
            timeline_text = match.group(0)
            datetime_obj = self._parse_timeline_to_datetime(match, pattern_type)
            
            return {
                'timeline_text': timeline_text,
                'datetime': datetime_obj,
                'confidence': min(priority / 100.0, 1.0),
                'type': pattern_type,
                'raw_match': match.groups()
            }
        
        # Default behavior based on message content
        return self._get_default_timeline(message_lower)
    
    def _parse_timeline_to_datetime(self, match: re.Match, pattern_type: str) -> Optional[datetime]:
        """Parse a matched timeline pattern to a datetime object"""
        
        if pattern_type == 'specific_time':
            return self._parse_specific_time(match)
        elif pattern_type == 'hours':
            hours = int(match.group(1))
            return self.now + timedelta(hours=hours)
        elif pattern_type == 'minutes':
            minutes = int(match.group(1))
            return self.now + timedelta(minutes=minutes)
        elif pattern_type == 'days':
            days = int(match.group(1))
            return self.now + timedelta(days=days)
        elif pattern_type == 'weeks':
            weeks = int(match.group(1))
            return self.now + timedelta(weeks=weeks)
        elif pattern_type == 'months':
            months = int(match.group(1))
            # Approximate months as 30 days
            return self.now + timedelta(days=months * 30)
        elif pattern_type == 'next_week':
            # Next Monday at 12:00 PM
            days_ahead = 7 - self.now.weekday()  # Monday is 0
            if days_ahead == 0:  # If today is Monday, get next Monday
                days_ahead = 7
            next_monday = self.now + timedelta(days=days_ahead)
            return datetime.combine(next_monday.date(), time(12, 0))
        elif pattern_type == 'next_month':
            # First day of next month at 12:00 PM
            if self.now.month == 12:
                next_month = self.now.replace(year=self.now.year + 1, month=1, day=1)
            else:
                next_month = self.now.replace(month=self.now.month + 1, day=1)
            return datetime.combine(next_month.date(), time(12, 0))
        elif pattern_type == 'next_year':
            # January 1st of next year at 12:00 PM
            next_year = self.now.replace(year=self.now.year + 1, month=1, day=1)
            return datetime.combine(next_year.date(), time(12, 0))
        elif pattern_type == 'tomorrow':
            return datetime.combine(self.tomorrow, time(12, 0))
        elif pattern_type == 'today':
            return datetime.combine(self.today, time(12, 0))
        elif pattern_type == 'this_week':
            # This Friday at 12:00 PM
            days_ahead = 4 - self.now.weekday()  # Friday is 4
            if days_ahead < 0:  # If past Friday, get next Friday
                days_ahead += 7
            this_friday = self.now + timedelta(days=days_ahead)
            return datetime.combine(this_friday.date(), time(12, 0))
        elif pattern_type == 'this_month':
            # 15th of this month at 12:00 PM
            this_month_15th = self.now.replace(day=15)
            return datetime.combine(this_month_15th.date(), time(12, 0))
        elif pattern_type == 'this_year':
            # June 15th of this year at 12:00 PM
            this_year_june = self.now.replace(month=6, day=15)
            return datetime.combine(this_year_june.date(), time(12, 0))
        elif pattern_type == 'few_hours':
            return self.now + timedelta(hours=2)  # Default to 2 hours
        elif pattern_type == 'few_days':
            return self.now + timedelta(days=3)  # Default to 3 days
        elif pattern_type == 'few_weeks':
            return self.now + timedelta(weeks=2)  # Default to 2 weeks
        elif pattern_type == 'few_months':
            return self.now + timedelta(days=60)  # Default to ~2 months
        elif pattern_type in ['later', 'soon']:
            return self.now + timedelta(hours=1)  # Default to 1 hour
        
        return None
    
    def _parse_specific_time(self, match: re.Match) -> Optional[datetime]:
        """Parse specific time expressions"""
        groups = match.groups()
        
        try:
            if len(groups) >= 3 and groups[2]:  # Has AM/PM
                hour = int(groups[0])
                minute = int(groups[1])
                am_pm = groups[2].lower()
                
                # Convert to 24-hour format
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                # Determine date (today or tomorrow)
                target_date = self.today
                if hour < self.now.hour or (hour == self.now.hour and minute <= self.now.minute):
                    target_date = self.tomorrow
                
                return datetime.combine(target_date, time(hour, minute))
            
            elif len(groups) >= 2 and groups[1]:  # Has AM/PM without minutes
                hour = int(groups[0])
                am_pm = groups[1].lower()
                
                # Convert to 24-hour format
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                # Determine date (today or tomorrow)
                target_date = self.today
                if hour < self.now.hour:
                    target_date = self.tomorrow
                
                return datetime.combine(target_date, time(hour, 0))
            
            elif len(groups) >= 2:  # 24-hour format
                hour = int(groups[0])
                minute = int(groups[1])
                
                # Determine date (today or tomorrow)
                target_date = self.today
                if hour < self.now.hour or (hour == self.now.hour and minute <= self.now.minute):
                    target_date = self.tomorrow
                
                return datetime.combine(target_date, time(hour, minute))
            
            elif groups[0] in ['noon', 'midnight']:
                target_date = self.today
                if groups[0] == 'noon':
                    hour = 12
                    minute = 0
                else:  # midnight
                    hour = 0
                    minute = 0
                
                # Determine date
                if hour < self.now.hour:
                    target_date = self.tomorrow
                
                return datetime.combine(target_date, time(hour, minute))
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing specific time: {e}")
            return None
        
        return None
    
    def _get_default_timeline(self, message_lower: str) -> Dict[str, Any]:
        """Get default timeline behavior based on message content"""
        
        # Check for reminder keywords
        if any(word in message_lower for word in ['remind', 'reminder']):
            # Default "remind me to..." behavior
            if any(word in message_lower for word in ['next week', 'next month', 'next year']):
                # If they mention a period but no specific time, use 12:00 PM
                if 'next week' in message_lower:
                    days_ahead = 7 - self.now.weekday()
                    if days_ahead == 0:
                        days_ahead = 7
                    next_monday = self.now + timedelta(days=days_ahead)
                    return {
                        'timeline_text': 'next week',
                        'datetime': datetime.combine(next_monday.date(), time(12, 0)),
                        'confidence': 0.7,
                        'type': 'next_week_default'
                    }
                elif 'next month' in message_lower:
                    if self.now.month == 12:
                        next_month = self.now.replace(year=self.now.year + 1, month=1, day=1)
                    else:
                        next_month = self.now.replace(month=self.now.month + 1, day=1)
                    return {
                        'timeline_text': 'next month',
                        'datetime': datetime.combine(next_month.date(), time(12, 0)),
                        'confidence': 0.7,
                        'type': 'next_month_default'
                    }
            
            # Default "remind me to..." without specific time = tomorrow at 12:00 PM
            return {
                'timeline_text': 'tomorrow',
                'datetime': datetime.combine(self.tomorrow, time(12, 0)),
                'confidence': 0.5,
                'type': 'default_reminder'
            }
        
        # Default for other cases
        return {
            'timeline_text': 'unspecified',
            'datetime': None,
            'confidence': 0.0,
            'type': 'unspecified'
        }
    
    def format_timeline_response(self, timeline_data: Dict[str, Any]) -> str:
        """Format timeline data for user response"""
        if not timeline_data['datetime']:
            return timeline_data['timeline_text']
        
        dt = timeline_data['datetime']
        now = datetime.now()
        
        # Format based on how far in the future
        if dt.date() == now.date():
            if dt.hour == now.hour and dt.minute == now.minute:
                return "now"
            elif dt.hour == 12 and dt.minute == 0:
                return "today at noon"
            else:
                return f"today at {dt.strftime('%I:%M %p').lower()}"
        elif dt.date() == now.date() + timedelta(days=1):
            if dt.hour == 12 and dt.minute == 0:
                return "tomorrow at noon"
            else:
                return f"tomorrow at {dt.strftime('%I:%M %p').lower()}"
        else:
            return dt.strftime('%A, %B %d at %I:%M %p').lower()


# Convenience function for backward compatibility
def extract_timeline(message: str) -> str:
    """Extract timeline text from message (backward compatibility)"""
    extractor = TimelineExtractor()
    result = extractor.extract_timeline(message)
    return result['timeline_text']


def parse_timeline_to_datetime(message: str) -> Optional[datetime]:
    """Parse timeline from message to datetime object"""
    extractor = TimelineExtractor()
    result = extractor.extract_timeline(message)
    return result['datetime']


# Test function
def test_timeline_extraction():
    """Test the timeline extraction with various inputs"""
    extractor = TimelineExtractor()
    
    test_cases = [
        "remind me to call david",
        "remind me to call david tomorrow",
        "remind me to call david next week",
        "remind me to call david at 3pm",
        "remind me to call david at 3:30pm",
        "remind me to call david tomorrow at 2pm",
        "remind me to call david in 2 hours",
        "remind me to call david in a few hours",
        "remind me to call david later",
        "remind me to call david next month",
        "remind me to call david in 3 days",
        "remind me to call david at noon",
        "remind me to call david at midnight",
    ]
    
    print("🧪 Testing Timeline Extraction")
    print("=" * 60)
    
    for message in test_cases:
        result = extractor.extract_timeline(message)
        formatted = extractor.format_timeline_response(result)
        
        print(f"\nMessage: '{message}'")
        print(f"Timeline: '{result['timeline_text']}'")
        print(f"DateTime: {result['datetime']}")
        print(f"Formatted: '{formatted}'")
        print(f"Type: {result['type']} (confidence: {result['confidence']:.2f})")


if __name__ == "__main__":
    test_timeline_extraction()
