import os
import json
from typing import Dict, Any, Optional
import openai

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# LLM extraction call with JSON schema tool
INTENT_SCHEMA = {
  "type": "object",
  "properties": {
    "no_change": {"type":"boolean"},
    "company": {"type":"string"},
    "role": {"type":"string"},
    "city": {"type":"string"},
    "tags_add": {"type":"array","items":{"type":"string"}},
    "tags_remove": {"type":"array","items":{"type":"string"}},
    "confirmation_text": {"type":"string"},
    "confidence": {"type":"number","minimum":0,"maximum":1}
  },
  "required": ["confirmation_text", "confidence"]
}

def call_extract(snapshot: str, inbound_text: str) -> Optional[Dict[str, Any]]:
    """
    Call LLM to extract structured updates from inbound SMS text
    
    Args:
        snapshot: Current Airtable snapshot of person's data
        inbound_text: Raw SMS text from user
        
    Returns:
        Dictionary with extracted updates and confidence, or None if failed
    """
    if not OPENAI_API_KEY:
        print("OpenAI API key not configured")
        return None
    
    try:
        # Set up OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Prepare the prompt
        system_prompt = f"""You are an AI assistant that helps parse SMS updates about people's professional information.

Current information for this person:
{snapshot}

The user has sent this SMS: "{inbound_text}"

Your task is to extract any updates to their professional information and return a structured response.

Rules:
1. If the user says "no change" or similar, set no_change=true and confidence=1.0
2. Extract company, role, city changes if mentioned
3. For tags, identify any new tags to add or existing tags to remove
4. Write a clear confirmation_text that summarizes what you understood
5. Set confidence based on how clear the user's intent is (0.0-1.0)
6. If confidence < 0.6, the system will ask for clarification

Return a JSON object matching this schema:
{json.dumps(INTENT_SCHEMA, indent=2)}

Example responses:
- For "no change": {{"no_change": true, "confirmation_text": "No changes needed.", "confidence": 1.0}}
- For "I left Google and now work at Microsoft as a PM": {{"company": "Microsoft", "role": "PM", "confirmation_text": "I understand you left Google and now work at Microsoft as a PM.", "confidence": 0.9}}
- For "moved to NYC": {{"city": "NYC", "confirmation_text": "I understand you moved to NYC.", "confidence": 0.8}}"""

        # Make the API call
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent parsing
            max_tokens=500
        )
        
        # Extract the response content
        content = response.choices[0].message.content
        
        # Parse the JSON response
        try:
            result = json.loads(content)
            
            # Validate required fields
            if "confirmation_text" not in result or "confidence" not in result:
                print("LLM response missing required fields")
                return None
            
            # Ensure confidence is a number
            if isinstance(result["confidence"], str):
                try:
                    result["confidence"] = float(result["confidence"])
                except ValueError:
                    result["confidence"] = 0.5
            
            # Set default values for optional fields
            if "no_change" not in result:
                result["no_change"] = False
            
            print(f"LLM extraction successful: {result}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {content}")
            return None
            
    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in LLM extraction: {e}")
        return None

def extract_with_fallback(snapshot: str, inbound_text: str) -> Dict[str, Any]:
    """
    Extract updates with fallback logic if LLM fails
    
    Args:
        snapshot: Current Airtable snapshot
        inbound_text: Raw SMS text
        
    Returns:
        Dictionary with extracted updates (may be basic fallback)
    """
    # Try LLM extraction first
    llm_result = call_extract(snapshot, inbound_text)
    
    if llm_result:
        return llm_result
    
    # Fallback: basic keyword matching
    text_lower = inbound_text.lower()
    
    # Check for "no change" patterns
    no_change_patterns = ["no change", "no changes", "nothing changed", "same", "all good", "correct"]
    if any(pattern in text_lower for pattern in no_change_patterns):
        return {
            "no_change": True,
            "confirmation_text": "I understand no changes are needed.",
            "confidence": 0.8
        }
    
    # Check for "stop" or opt-out
    if "stop" in text_lower:
        return {
            "no_change": False,
            "confirmation_text": "You have been unsubscribed from monthly check-ins.",
            "confidence": 0.9
        }
    
    # Very basic fallback
    return {
        "no_change": False,
        "confirmation_text": "I received your message but need more context. Please provide specific details about what changed.",
        "confidence": 0.3
    }
