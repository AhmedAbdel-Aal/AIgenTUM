scrap_chair_page_prompt = """You are an expert at analyzing HTML content for academic websites. Given the following HTML from a university chair's webpage: {html_string}

Please extract and organize the following specific information:

1. Subsections:
- Extract all URLs/links related in the provided HTML
- give a hint about the content of the link

2. Home page content summary:
- Extract and summarize all the text content from the home page
- Include any relevant information about the chair, research, or team

2. (if availble) Open Positions:
- Extract all URLs/links related to job openings, positions, or career opportunities
- Include both direct position links and links to general job portals if present

3. (if availble) Research Interests:
- List all stated research interests and focus areas
- Include both current and planned research directions
- Extract any specific topics, methodologies, or domains mentioned

4. (if availble) Research Activities:
- Extract information about ongoing research projects
- Include any published works or significant research outputs
- Note any collaborations or research partnerships

Please format the response in json format:

If any section cannot be found, please indicate with "Not found in provided HTML".
"""


def get_chair_scrapping_prompt(url):
    chair_scrapping_prompt =  f"""
You are an expert at analyzing university webpages for thesis opportunities.
    
URL to analyze: {url}

To analyze this webpage, you need to:
1. Extract and analyze links
2. Scrape content from relevant pages
3. Structure the found information

Use the following format:

Thought: First, I need to understand what links are available on the main page.
Action: link_extractor
Action Input: {url}

Thought: Now that I have the links, I should check the content of relevant pages.
Action: web_page_scraper
Action Input: [URL from previous step]

Thought: Let me analyze another relevant page...
Action: web_page_scraper
Action Input: [Another relevant URL]

... continue until all relevant information is gathered ...

Thought: I have gathered all the information. Let me structure it.
Final Answer: Present the information in this structure:

CHAIR INFORMATION:
- Chair/Department Name:
- Website:
- General Contact:
- Application Process:
- General Requirements:
- Research Areas:

THESIS OPPORTUNITIES:
For each thesis found:
**Opportunity**
- Type: [Master thesis, Bachelor thesis, Project]
- Title:
- Description:
- URL:
- Contact Person:
- Research Fields:
- Technical Requirements:
- Academic Requirements:
- Timeline:
- Additional Information:

Remember:
1. Keep URLs absolute
2. Include ALL found thesis opportunities
3. Be explicit about missing information
4. Keep proper formatting and sections
        """
    return chair_scrapping_prompt
