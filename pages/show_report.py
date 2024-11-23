# pages/show_report.py
import streamlit as st
from pathlib import Path
from matching_agent import ThesisMatchingAgent
import time
from datetime import datetime

def init_session_state():
    """Initialize session state variables"""
    if 'student_id' not in st.session_state:
        st.session_state.student_id = None
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None
    if 'processed_chairs' not in st.session_state:
        st.session_state.processed_chairs = []
    if 'matching_complete' not in st.session_state:
        st.session_state.matching_complete = False
    if 'report_path' not in st.session_state:
        st.session_state.report_path = None

def display_matching_report(report_path: Path) -> None:
    """Display the matching report with proper markdown structure"""
    try:
        with open(report_path, 'r') as f:
            report_content = f.read()
        
        # Split into profile and matches
        main_sections = report_content.split("TOP THESIS MATCHES")
        
        # Display student profile
        profile_lines = [line.strip() for line in main_sections[0].split('\n') if line.strip()]
        with st.expander("📋 Student Profile", expanded=True):
            for line in profile_lines:
                if ':' in line and not line.startswith('Generated'):
                    key, value = line.split(':', 1)
                    if not any(x in key for x in ['SUMMARY', '---']):
                        st.markdown(f"**{key.strip()}:** {value.strip()}")

        # Display matches header
        st.markdown("## 🎯 Top Thesis Matches")
        
        # Split and process each match
        matches = main_sections[1].split("--------------------------------------------------------------------------------")
        
        for match in matches:
            if not match.strip():
                continue
            
            # Split match content into lines
            lines = [line.strip() for line in match.split('\n') if line.strip()]
            
            # Extract title and score
            title_line = next((line for line in lines if line.startswith(('1.', '2.', '3.', '4.', '5.'))), None)
            if not title_line:
                continue
                
            title = title_line.split('.', 1)[1].split('(')[0].strip()
            score = title_line.split('(')[1].split('%')[0].strip()
            
            # Create match expander
            with st.expander(f"### {title} - {score[-2:]}%", expanded=False):
                # Header section with score and chair
                col1, col2 = st.columns([2,1])
                with col1:
                    chair_line = next(line for line in lines if line.startswith('Chair:'))
                    st.markdown(f"**{chair_line}**")
                with col2:
                    st.markdown(f"""
                        <div class='score-box'>
                            <h3>{score[-2:]}% Match</h3>
                        </div>
                    """, unsafe_allow_html=True)                
                st.markdown("---")
                
                # Process main sections
                current_section = None
                section_content = []
                
                for line in lines:
                    if line.startswith(('2.', '3.', '4.', '5.')):  # Main section headers
                        # Output previous section if exists
                        if current_section and section_content:
                            st.markdown(f"### {current_section}")
                            st.markdown('\n'.join(section_content))
                        # Start new section
                        current_section = line.split(':', 1)[0].strip('12345. ')
                        section_content = []
                    elif line.startswith('**') or line.startswith('-'):  # Subsections and bullet points
                        section_content.append(line)
                    elif line.startswith('Analysis:') or line.startswith('1. Match'):
                        continue
                    elif line and not line.startswith('Chair:') and not line.startswith('URL:'):
                        section_content.append(line)
                
                # Output last section
                if current_section and section_content:
                    st.markdown(f"### {current_section}")
                    st.markdown('\n'.join(section_content))

        # Add download button
        st.markdown("---")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.download_button(
                label="📥 Download Complete Report",
                data=report_content,
                file_name=f"thesis_matching_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
    except Exception as e:
        st.error(f"Error displaying report: {str(e)}")

# Add this styling to your main function
def apply_custom_styles():
    st.markdown("""
        <style>
        .stExpander {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stExpander > div:first-child {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Main text color */
        .stMarkdown, p, span, li {
            color: rgba(255, 255, 255, 0.9) !important;
        }
        
        /* Headers */
        h2 {
            color: rgba(255, 255, 255, 0.95) !important;
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        h3 {
            color: rgba(255, 255, 255, 0.95) !important;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            font-weight: 600;
        }
        
        /* Bold text */
        strong {
            color: rgba(255, 255, 255, 1) !important;
            font-weight: 600;
        }
        
        /* Lists */
        ul {
            margin-left: 1.5rem;
            margin-bottom: 1rem;
            color: rgba(255, 255, 255, 0.9) !important;
        }
        
        li {
            margin-bottom: 0.5rem;
            color: rgba(255, 255, 255, 0.9) !important;
        }
        
        /* Score box */
        .score-box {
            background-color: rgba(0, 102, 204, 0.2);
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        
        .score-box h3 {
            margin: 0;
            color: rgba(255, 255, 255, 0.95) !important;
        }
        
        /* General text settings */
        .stMarkdown {
            line-height: 1.6;
        }
        
        /* Dividers */
        hr {
            margin: 1.5rem 0;
            border: 0;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Download button */
        .stDownloadButton button {
            background-color: #2ea44f;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 1px 0 rgba(0, 0, 0, 0.1);
            transition: background-color 0.2s;
        }
        
        .stDownloadButton button:hover {
            background-color: #2c974b;
        }

        /* Expander text */
        .stExpander p {
            color: rgba(255, 255, 255, 0.9) !important;
        }
        
        /* Fix for expander headers */
        .stExpander > div:first-child > div {
            color: rgba(255, 255, 255, 0.95) !important;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)


def generate_matching_report():
    """Generate the matching report using the ThesisMatchingAgent"""
    try:
        with st.spinner("🔄 Generating final matching report..."):
            # Create paths
            student_dir = Path(f"student_data/{st.session_state.student_id}")
            thesis_data_dir = Path(f"thesis_data/{st.session_state.student_id}")
            print(student_dir, thesis_data_dir)
            # Initialize matcher
            matcher = ThesisMatchingAgent(st.session_state.openai_api_key)
            
            # Run matching
            result_path = matcher.run_matching(student_dir, thesis_data_dir)
            
            # Store report path in session state
            st.session_state.report_path = result_path
            st.session_state.matching_complete = True
            
            return True
            
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
        return False

def main():
    
    # Page config
    st.set_page_config(page_title="Thesis Matches", page_icon="🎯", layout="wide")
    init_session_state()
    apply_custom_styles()    
    
    # Verify prerequisites
    if not st.session_state.student_id:
        st.error("Please complete your profile first!")
        if st.button("Return to Profile"):
            st.switch_page("Home.py")
        st.stop()
    
    if not st.session_state.processed_chairs:
        st.error("No chair data available! Please complete the matching process.")
        if st.button("Return to Matching"):
            st.switch_page("pages/matching_progress.py")
        st.stop()
    
    # Generate or display report
    if not st.session_state.matching_complete:
        st.title("🎯 Generating Your Thesis Matches")
        if generate_matching_report():
            st.success("Report generated successfully!")
            time.sleep(1)
            st.rerun()
    else:
        st.title("🎯 Your Thesis Matches")

        if st.session_state.report_path:
            display_matching_report(Path(st.session_state.report_path))
        else:
            st.error("Report not found! Please try generating it again.")
            if st.button("Regenerate Report"):
                st.session_state.matching_complete = False
                st.rerun()
if __name__ == "__main__":
    main()