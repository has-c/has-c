#!/usr/bin/env python3
import json
import re
import urllib.request
import urllib.error
import os

# Fetch quote from Gemini API
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY secret is not set")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

prompt = """Generate an inspirational quote from a famous mathematician, statistician, or computer scientist. 
Format your response as valid JSON with exactly these fields:
{
  "quote": "the quote text",
  "author": "author name",
  "field": "mathematics/statistics/computer science"
}
Only return the JSON object, no additional text or markdown formatting."""

payload = json.dumps({
    "contents": [{
        "parts": [{"text": prompt}]
    }]
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
with open('README.md', 'r') as f:
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
    # Add quote section after the header
    header_match = re.match(r'(.*?## Hi there 👋\n)', content, re.DOTALL)
    if header_match:
        new_content = header_match.group(1) + '\n' + quote_section + '\n\n' + content[header_match.end():]
    else:
        new_content = quote_section + '\n\n' + content

# Write updated README
with open('README.md', 'w') as f:
    f.write(new_content)

print("README updated successfully!")

