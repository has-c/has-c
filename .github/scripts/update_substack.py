#!/usr/bin/env python3
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# Substack RSS feed URL
rss_url = "https://highstreetcapital.substack.com/feed"

try:
    # Fetch RSS feed
    with urllib.request.urlopen(rss_url) as response:
        rss_content = response.read().decode('utf-8')
    
    # Parse XML
    root = ET.fromstring(rss_content)
    
    # Find all items (posts)
    items = root.findall('.//item')[:3]  # Get latest 3 posts
    
    posts_list = []
    for item in items:
        title_elem = item.find('title')
        link_elem = item.find('link')
        
        if title_elem is not None and link_elem is not None:
            title = title_elem.text.strip()
            link = link_elem.text.strip()
            posts_list.append(f"- [{title}]({link})")
    
    if posts_list:
        posts_section = '\n'.join(posts_list)
    else:
        posts_section = "- No posts found"

except Exception as e:
    print(f"Error fetching Substack posts: {e}")
    posts_section = "- Error loading posts"

# Read README
with open('README.md', 'r') as f:
    content = f.read()

# Create posts section with markers
posts_section_with_markers = f"""<!-- SUBSTACK POSTS -->
{posts_section}
<!-- /SUBSTACK POSTS -->"""

# Pattern to match the posts section between markers
pattern = r'<!-- SUBSTACK POSTS -->.*?<!-- /SUBSTACK POSTS -->'

if re.search(pattern, content, re.DOTALL):
    # Replace existing posts
    new_content = re.sub(pattern, posts_section_with_markers, content, flags=re.DOTALL)
else:
    # Add posts section if not found (shouldn't happen, but fallback)
    new_content = content + '\n\n' + posts_section_with_markers

# Write updated README
with open('README.md', 'w') as f:
    f.write(new_content)

print("Substack posts updated successfully!")

