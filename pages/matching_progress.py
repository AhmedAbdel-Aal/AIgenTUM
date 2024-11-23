# pages/matching_progress.py
import streamlit as st
import time
import json
import random
from pathlib import Path
from scrapping_agent import create_thesis_opportunities_agent
from prompts import get_chair_scrapping_prompt

class MatchingProgress:
    def __init__(self, openai_api_key: str):
        # Load chairs data
        with open('chairs_data.json', 'r') as f:
            chairs_dict = json.load(f)
            
        # Filter out non-chair entries and get random sample
        self.chairs_data = {
            k: v for k, v in chairs_dict.items() 
            if k in ['Quantum Computing', 'Theoretical Foundations of Artificial Intelligence', 'Information Systems and Business Process Management']
        }

        self.selected_chairs = random.sample(list(self.chairs_data.keys()), 2)
        
        # Initialize agents
        self.scraping_agent = create_thesis_opportunities_agent(openai_api_key)
        
        # Create directory for scraped data if it doesn't exist
        self.thesis_data_dir = Path("thesis_data")
        self.thesis_data_dir.mkdir(exist_ok=True)

    def scrape_chair(self, chair_name: str, url: str) -> dict:
        """Scrape thesis opportunities from a chair's website"""
        try:
            prompt = get_chair_scrapping_prompt(url)
            result = self.scraping_agent.run(prompt)
            
            # Save the scraped data
            chair_file = self.thesis_data_dir / f"{chair_name.lower().replace(' ', '_')}.txt"
            with open(chair_file, 'w', encoding='utf-8') as f:
                f.write(result)

            # Also save to student-specific directory for tracking
            student_thesis_dir = Path(f"thesis_data/{st.session_state.student_id}")
            student_thesis_dir.mkdir(parents=True, exist_ok=True)
            
            file_name = f"opp_{chair_name.lower().replace(' ', '_')}.txt"
            student_chair_file = student_thesis_dir / file_name
            with open(student_chair_file, 'a', encoding='utf-8') as f:
                f.write(result)


            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run(self):
        st.title("🔍 Matching Your Profile")
        
        # Center content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.write("### Analyzing your profile across department chairs...")
            
            progress_bar = st.progress(0)
            status = st.empty()
            chairs_list = st.empty()
            matches = st.empty()
            
            successful_scrapes = []
            processed_chairs = []
            
            for i, chair in enumerate(self.selected_chairs):
                # Update progress
                progress = (i + 1) / len(self.selected_chairs)
                progress_bar.progress(progress)
                
                # Get chair URL
                chair_url = self.chairs_data[chair]["link"]
                chair_professor = self.chairs_data[chair]["professor"]
                
                # Update status
                status.markdown(f"""### 🔄 Processing: {chair}
                Professor: {chair_professor}
                URL: {chair_url}""")
                
                # Scrape chair data
                result = self.scrape_chair(chair, chair_url)
                
                if result["success"]:
                    successful_scrapes.append(chair)
                
                processed_chairs.append(chair)
                chairs_list.markdown("### Processed Chairs:\n" + "\n".join([
                    f"✓ {c} {'✅' if c in successful_scrapes else '❌'}" 
                    for c in processed_chairs
                ]))
                
                matches.markdown(f"### 🎯 Successful Scrapes: {len(successful_scrapes)}")
                
                # Add some delay for visual effect
                time.sleep(1)
            
            # Final success message
            st.success(f"""
            ### 🎉 Data Collection Complete!
            
            - Processed {len(processed_chairs)} chairs
            - Successfully scraped {len(successful_scrapes)} chairs
            - Ready to analyze matches
            
            Proceeding to matching analysis...
            """)
            
            # Save processed chairs to session state for the matching phase
            st.session_state.processed_chairs = successful_scrapes
            
            # Brief delay before redirect
            time.sleep(3)
            st.switch_page("pages/show_report.py")

def init_session_state():
    """Initialize session state variables"""
    if 'student_data' not in st.session_state:
        st.session_state.student_data = None
    if 'processed_chairs' not in st.session_state:
        st.session_state.processed_chairs = []
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None

if __name__ == "__main__":
    # Page config
    st.set_page_config(
        page_title="Thesis Matching Progress",
        page_icon="🔍",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Check prerequisites
    if not st.session_state.student_data:
        st.error("Please complete your profile first!")
        if st.button("Return to Profile"):
            st.switch_page("Home.py")
    elif not st.session_state.openai_api_key:
        st.error("OpenAI API key not found!")
        if st.button("Return to Setup"):
            st.switch_page("Home.py")
    else:
        progress = MatchingProgress(st.session_state.openai_api_key)
        progress.run()