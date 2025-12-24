#!/usr/bin/env python3
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

# Try different Substack RSS feed URL formats
rss_urls = [
    "https://highstreetcapital.substack.com/feed",
    "https://substack.com/@highstreetcapital/feed",
    "https://highstreetcapital.substack.com/rss"
]

posts_section = "- Error loading posts"

for rss_url in rss_urls:
    try:
        print(f"Trying RSS URL: {rss_url}")
        # Fetch RSS feed with timeout
        req = urllib.request.Request(rss_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            rss_content = response.read().decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(rss_content)
        
        # Find all items (posts) - handle both RSS 2.0 and Atom formats
        items = root.findall('.//item')[:3]  # RSS 2.0 format
        if not items:
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')[:3]  # Atom format
        
        posts_list = []
        for item in items:
            # Try RSS 2.0 format first
            title_elem = item.find('title')
            link_elem = item.find('link')
            
            # If Atom format
            if title_elem is None:
                title_elem = item.find('{http://www.w3.org/2005/Atom}title')
            if link_elem is None:
                link_elem = item.find('{http://www.w3.org/2005/Atom}link')
                if link_elem is not None:
                    link_elem.text = link_elem.get('href', '')
            
            if title_elem is not None and link_elem is not None:
                title = title_elem.text.strip() if title_elem.text else ""
                link = link_elem.text.strip() if link_elem.text else link_elem.get('href', '').strip()
                if title and link:
                    posts_list.append(f"- [{title}]({link})")
        
        if posts_list:
            posts_section = '\n'.join(posts_list)
            print(f"Successfully fetched {len(posts_list)} posts from {rss_url}")
            break
        else:
            print(f"No posts found in {rss_url}")
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {rss_url}: {e.reason}")
        continue
    except urllib.error.URLError as e:
        print(f"URL Error for {rss_url}: {e.reason}")
        continue
    except ET.ParseError as e:
        print(f"XML Parse Error for {rss_url}: {e}")
        continue
    except Exception as e:
        print(f"Error fetching from {rss_url}: {e}")
        continue

if posts_section == "- Error loading posts":
    print("All RSS URLs failed, using fallback message")

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

