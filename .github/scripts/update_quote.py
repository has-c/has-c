#!/usr/bin/env python3
import json
import re
import urllib.request
import urllib.error
import os
from datetime import datetime

# Fetch quote from Gemini API
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY secret is not set")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

# Generate a unique seed based on current time for variety
current_time = datetime.now()
seed = int(current_time.timestamp() * 1000) % 2147483647  # Keep within int32 range

# Theme rotation based on day of year for variety
themes = [
    "pure mathematics and number theory",
    "algorithms and computational complexity",
    "statistics and probability",
    "logic and foundations",
    "geometry and topology",
    "artificial intelligence and machine learning",
    "cryptography and security",
    "data science and analytics",
    "software engineering wisdom",
    "physics and applied mathematics"
]
theme = themes[current_time.timetuple().tm_yday % len(themes)]

# Era rotation for author variety
eras = [
    "ancient or medieval (before 1600)",
    "classical (1600-1900)",
    "early modern (1900-1970)",
    "contemporary (1970-present)"
]
era = eras[current_time.hour % len(eras)]

prompt = f"""Generate a unique, thought-provoking quote from a mathematician, statistician, or computer scientist.

REQUIREMENTS FOR VARIETY:
- Focus on: {theme}
- Prefer authors from: {era} era
- The quote should be genuinely insightful, not a cliché
- Pick real, verifiable quotes ALWAYS

Format your response as valid JSON with exactly these fields:
{{
  "quote": "the quote text",
  "author": "author name",
  "field": "their primary field"
}}
Only return the JSON object, no additional text or markdown formatting."""

payload = json.dumps({
    "contents": [{
        "parts": [{"text": prompt}]
    }],
    "generationConfig": {
        "temperature": 1.0,  # Controls randomness (0.0-2.0, 1.0 recommended)
        "topP": 0.95,        # Nucleus sampling - consider tokens comprising top 95% probability
        "topK": 40,          # Consider top 40 most likely tokens
        "seed": seed         # Unique seed for each run to ensure different outputs
    }
}).encode('utf-8')

headers = {"Content-Type": "application/json"}

try:
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    # Extract text from Gemini response
    text = data['candidates'][0]['content']['parts'][0]['text'].strip()
    
    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Parse JSON
    try:
        quote_data = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object from text
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        if json_match:
            quote_data = json.loads(json_match.group())
        else:
            quote_data = {
                "quote": "No quote found",
                "author": "System",
                "field": "error"
            }
    
    quote = quote_data.get('quote', 'No quote found')
    author = quote_data.get('author', 'Unknown')
    field = quote_data.get('field', 'unknown')

except Exception as e:
    print(f"Error fetching quote: {e}")
    quote = "No quote found"
    author = "System"
    field = "error"

# Read README
with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Create quote section with closing marker
quote_section = f"""<!-- DAILY QUOTE -->
> {quote}
> 
> — *{author}* ({field})
<!-- /DAILY QUOTE -->"""

# Pattern to match the quote section between markers
pattern = r'<!-- DAILY QUOTE -->.*?<!-- /DAILY QUOTE -->'

if re.search(pattern, content, re.DOTALL):
    # Replace existing quote
    new_content = re.sub(pattern, quote_section, content, flags=re.DOTALL)
else:
    # Add quote section after the intro
    header_match = re.match(r'(#.*?\n\n\*\*.*?\*\*.*?\n)', content, re.DOTALL)
    if header_match:
        new_content = header_match.group(1) + '\n' + quote_section + '\n\n' + content[header_match.end():]
    else:
        new_content = quote_section + '\n\n' + content

# Write updated README
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("README updated successfully!")

