import streamlit as st
from openai import OpenAI
from pathlib import Path
import json
import PyPDF2
from datetime import datetime
import os
from typing import Dict, Any
import uuid
import random
import time

# load dotenv
from dotenv import load_dotenv
load_dotenv()

class StudentAgent:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.data_dir = Path("student_data")
        self.data_dir.mkdir(exist_ok=True)

        self.chairs = [
            "Chair of Software Engineering",
            "Chair of Robotics",
            "Chair of Artificial Intelligence",
            "Chair of Data Science",
            "Chair of Computer Vision",
            "Chair of Machine Learning",
            "Chair of Computer Graphics",
            "Chair of Distributed Systems"
        ]
        
        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_student_id' not in st.session_state:
            st.session_state.current_student_id = str(uuid.uuid4())
        if 'student_data' not in st.session_state:
            st.session_state.student_data = {
                "personal_info": {},
                "interests": [],
                "preferred_topics": [],
                "skills": [],
                "cv_path": None,
                "cv_summary": None,
                "transcript_path": None,
                "transcript_summary": None,
                "courses": [],
                "gpa": None,
                "motivation_letter_path": None,
                "motivation_letter_summary": None,
                "motivation_letter_feedback": None
            }
        if 'conversation_stage' not in st.session_state:
            st.session_state.conversation_stage = "initial"
        if 'awaiting_confirmation' not in st.session_state:
            st.session_state.awaiting_confirmation = False
        if 'cv_uploaded' not in st.session_state:
            st.session_state.cv_uploaded = False
        if 'transcript_uploaded' not in st.session_state:
            st.session_state.transcript_uploaded = False
        if 'motivation_letter_uploaded' not in st.session_state:
            st.session_state.motivation_letter_uploaded = False
        if 'confirm_message_displayed' not in st.session_state:
            st.session_state.confirm_message_displayed = False


    def save_uploaded_file(self, uploaded_file, file_type: str) -> Path:
        """Save uploaded file and return the path."""
        student_dir = self.data_dir / st.session_state.current_student_id
        student_dir.mkdir(exist_ok=True)
        
        file_path = student_dir / f"{file_type}_{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF file."""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def summarize_cv(self, cv_text: str) -> str:
        """Use OpenAI to summarize CV content."""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing CVs. Summarize the key points including education, skills, and experience."},
                {"role": "user", "content": f"Please summarize this CV:\n\n{cv_text}"}
            ]
        )
        return response.choices[0].message.content

    def clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text from PDF."""
        # Split into lines and remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Join words that were incorrectly split
        cleaned_text = ""
        buffer = []
        
        for line in lines:
            # If line ends with a period, question mark, or exclamation mark, it's likely a sentence end
            if line.endswith(('.', '?', '!')):
                buffer.append(line)
                cleaned_text += ' '.join(buffer) + '\n\n'
                buffer = []
            # If line has just one word and the next line might be a continuation
            elif len(line.split()) <= 2:
                buffer.append(line)
            else:
                buffer.append(line)
                cleaned_text += ' '.join(buffer) + '\n\n'
                buffer = []
        
        # Add any remaining text
        if buffer:
            cleaned_text += ' '.join(buffer)
        
        # Clean up spacing
        cleaned_text = ' '.join(cleaned_text.split())
        
        # Add proper paragraph breaks
        cleaned_text = cleaned_text.replace('. ', '.\n\n')
        
        return cleaned_text

    def analyze_transcript(self, transcript_text: str) -> dict:
        """Use OpenAI to analyze transcript and extract courses and grades."""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
You are an expert at analyzing academic transcripts. Extract and organize the following information:
1. List of all courses with their grades (in the format: Course Name: Grade)
2. Calculate the overall GPA if possible
3. Identify key areas of study
4. Note any honors or distinctions

Provide the information in a JSON format with the following structure:
{
    "courses": [{"name": "Course Name", "grade": "Grade"}],
    "gpa": "X.XX",
    "key_areas": ["Area1", "Area2"],
    "honors": ["Honor1", "Honor2"]
}
"""},
                {"role": "user", "content": f"Please analyze this transcript:\n\n{transcript_text}"}
            ]
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "courses": [],
                "gpa": None,
                "key_areas": [],
                "honors": []
            }

    def format_transcript_summary(self, analysis: dict) -> str:
        """Format transcript analysis into a readable summary."""
        summary = "📚 Transcript Analysis:\n\n"
        
        if analysis.get("courses"):
            summary += "Courses and Grades:\n"
            for course in analysis["courses"]:
                summary += f"- {course['name']}: {course['grade']}\n"
            summary += "\n"
        
        if analysis.get("gpa"):
            summary += f"Overall GPA: {analysis['gpa']}\n\n"
        
        if analysis.get("key_areas"):
            summary += "Key Areas of Study:\n"
            for area in analysis["key_areas"]:
                summary += f"- {area}\n"
            summary += "\n"
        
        if analysis.get("honors"):
            summary += "Honors and Distinctions:\n"
            for honor in analysis["honors"]:
                summary += f"- {honor}\n"
            
        return summary

    def get_next_question(self, context: Dict[str, Any]) -> str:
        """Generate next question based on conversation stage and context."""
        prompts = {
            "initial": "Hi! I'm your thesis matching assistant. To help you find the perfect thesis opportunity, I'll need to learn more about you. Please upload both your CV and academic transcript.",
            "cv_uploaded": "Great! I've processed your documents. Could you tell me about your main areas of interest in your field of study?",
            "interests_shared": "What specific topics would you like to work on for your thesis? You can list multiple topics.",
            "topics_shared": "What technical skills do you have that you'd like to apply in your thesis work?",
            "skills_shared": "Is there anything specific you're looking for in a thesis advisor or research group?",
            "completed": """
Perfect! I've gathered all the necessary information about your profile. Here's a summary of what I know:

1. Your CV and transcript have been processed and analyzed
2. Academic Performance: {gpa} GPA
3. Key Courses: {key_courses}
4. Interests: {interests}
5. Preferred Topics: {topics}
6. Technical Skills: {skills}

I'm ready to start the matching process to find the best thesis opportunities for you. 
Please type 'confirm' to proceed with the matching process, or share any additional information you'd like me to consider."""
        }
        
        if context["stage"] == "completed":
            # Get top 3 courses by grade
            top_courses = sorted(
                st.session_state.student_data.get("courses", []),
                key=lambda x: x.get("grade", ""),
                reverse=True
            )[:3]
            top_courses_str = ", ".join([c["name"] for c in top_courses])
            
            return prompts["completed"].format(
                gpa=st.session_state.student_data.get("gpa", "Not available"),
                key_courses=top_courses_str,
                interests=", ".join(st.session_state.student_data["interests"]),
                topics=", ".join(st.session_state.student_data["preferred_topics"]),
                skills=", ".join(st.session_state.student_data["skills"])
            )
        return prompts.get(context["stage"], "Is there anything else you'd like to share about your thesis preferences?")




    def process_user_input(self, user_input: str) -> str:
        """Process user input and update student data."""                    
        if st.session_state.conversation_stage == "completed":
            if user_input.lower().strip() == "confirm":
                st.session_state.confirm_message_displayed = True
                return """
                        Thank you for confirming! 🎉 I'm now sending your profile to our matching system. 
                        The system will analyze:
                        - Your CV and academic background
                        - Your transcript and course performance
                        - Your stated interests and preferences
                        - Available thesis opportunities
                        - Requirements and alignments

                        You'll receive the matching results soon. Good luck with your thesis journey! 🌟

                        Note: This conversation has been saved and your profile is being processed."""
            
            # If not confirmed, treat as additional information
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing student responses and extracting relevant information for thesis matching."},
                    {"role": "user", "content": f"Process this additional information from the student: {user_input}"}
                ]
            )
            return response.choices[0].message.content + "\n\nPlease type 'confirm' when you're ready to proceed with the matching process."

        # Normal processing for other stages
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing student responses and extracting relevant information for thesis matching."},
                {"role": "user", "content": f"Process this student response and extract relevant information: {user_input}"}
            ]
        )
        
        # Update student data based on conversation stage
        if st.session_state.conversation_stage == "interests_shared":
            st.session_state.student_data["interests"].extend(
                [interest.strip() for interest in user_input.split(",") if interest.strip()]
            )
        elif st.session_state.conversation_stage == "topics_shared":
            st.session_state.student_data["preferred_topics"].extend(
                [topic.strip() for topic in user_input.split(",") if topic.strip()]
            )
        elif st.session_state.conversation_stage == "skills_shared":
            st.session_state.student_data["skills"].extend(
                [skill.strip() for skill in user_input.split(",") if skill.strip()]
            )
            
        return response.choices[0].message.content

    def save_student_data(self):
        """Save all student data to JSON file."""
        student_dir = self.data_dir / st.session_state.current_student_id
        student_dir.mkdir(exist_ok=True)
        
        data_path = student_dir / "student_data.json"
        with open(data_path, "w") as f:
            json.dump(st.session_state.student_data, f, indent=4)

    def run(self):
        st.title("Thesis Matching Assistant")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Display initial message if conversation is just starting
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown(self.get_next_question({"stage": "initial"}))
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": self.get_next_question({"stage": "initial"})
                })

        # Handle file uploads
        if st.session_state.conversation_stage == "initial":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cv_file = st.file_uploader("Upload your CV (PDF)", type="pdf", key="cv_upload")
                if cv_file and not st.session_state.cv_uploaded:
                    with st.spinner('Processing your CV...'):
                        cv_path = self.save_uploaded_file(cv_file, "cv")
                        cv_text = self.extract_text_from_pdf(cv_path)
                        cv_summary = self.summarize_cv(cv_text)
                        
                        st.session_state.student_data["cv_path"] = str(cv_path)
                        st.session_state.student_data["cv_summary"] = cv_summary
                        
                        summary_path = cv_path.parent / "cv_summary.txt"
                        with open(summary_path, "w") as f:
                            f.write(cv_summary)
                        
                        st.session_state.cv_uploaded = True
            
            with col2:
                transcript_file = st.file_uploader("Upload your Transcript (PDF)", type="pdf", key="transcript_upload")
                if transcript_file and not st.session_state.transcript_uploaded:
                    with st.spinner('Processing your transcript...'):
                        transcript_path = self.save_uploaded_file(transcript_file, "transcript")
                        transcript_text = self.extract_text_from_pdf(transcript_path)
                        transcript_analysis = self.analyze_transcript(transcript_text)
                        transcript_summary = self.format_transcript_summary(transcript_analysis)
                        
                        st.session_state.student_data["transcript_path"] = str(transcript_path)
                        st.session_state.student_data["transcript_summary"] = transcript_summary
                        st.session_state.student_data["courses"] = transcript_analysis.get("courses", [])
                        st.session_state.student_data["gpa"] = transcript_analysis.get("gpa")
                        
                        summary_path = transcript_path.parent / "transcript_summary.txt"
                        with open(summary_path, "w") as f:
                            f.write(transcript_summary)
                        
                        st.session_state.transcript_uploaded = True


            with col3:
                motivation_letter = st.file_uploader("Upload Motivation Letter (Optional)", type="pdf", key="motivation_upload")
                if motivation_letter and not st.session_state.motivation_letter_uploaded:
                    with st.spinner('Processing your motivation letter...'):
                        # Save PDF
                        letter_path = self.save_uploaded_file(motivation_letter, "motivation_letter")
                        
                        # Extract and clean text
                        raw_text = self.extract_text_from_pdf(letter_path)
                        cleaned_text = self.clean_extracted_text(raw_text)
                        
                        # Save cleaned text
                        text_path = letter_path.parent / "motivation_letter.txt"
                        with open(text_path, "w", encoding='utf-8') as f:
                            f.write(cleaned_text)
                        
                        # Update student data
                        st.session_state.student_data["motivation_letter_path"] = str(letter_path)
                        st.session_state.student_data["motivation_letter_text"] = cleaned_text
                        
                        st.session_state.motivation_letter_uploaded = True
            # Proceed when both files are uploaded
            if st.session_state.cv_uploaded and st.session_state.transcript_uploaded:
                combined_message = (
                    "I've processed both your CV and transcript. Here's what I understood:\n\n"
                    "From your CV:\n" + st.session_state.student_data["cv_summary"] + "\n\n"
                    "From your transcript:\n" + st.session_state.student_data["transcript_summary"] + "\n\n"
                    "Now, " + self.get_next_question({"stage": "cv_uploaded"})
                )
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": combined_message
                })
                
                st.session_state.conversation_stage = "cv_uploaded"
                st.rerun()

        # Get user input
        if prompt := st.chat_input("Your response"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Process user input and generate response
            response = self.process_user_input(prompt)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Update conversation stage
            if st.session_state.conversation_stage != "completed":
                stages = ["initial", "cv_uploaded", "interests_shared", "topics_shared", "skills_shared", "completed"]
                current_index = stages.index(st.session_state.conversation_stage)
                if current_index < len(stages) - 1:
                    st.session_state.conversation_stage = stages[current_index + 1]
                    
                    # Add next question if not completed
                    next_question = self.get_next_question({"stage": st.session_state.conversation_stage})
                    st.session_state.messages.append({"role": "assistant", "content": next_question})
            
# Handle confirmation
            if prompt.lower().strip() == "confirm" and st.session_state.conversation_stage == "completed":
                st.session_state.student_data["status"] = "confirmed"
                st.session_state.student_data["confirmation_time"] = datetime.now().isoformat()
                self.save_student_data()
                            # Set up required session states for matching progress
                st.session_state.openai_api_key = os.environ.get("OPENAI_API_KEY")
                st.session_state.student_id = st.session_state.current_student_id
                st.session_state.processing_started = True
                
                # Add a success message before transition
                st.success("Profile confirmed! Starting thesis matching process...")
                time.sleep(2)  # Brief pause for user to see the message
                
                # Redirect to matching progress page
                st.switch_page("pages/matching_progress.py")

            
            st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="Thesis Matching Assistant", page_icon="📚")
    
    # Get OpenAI API key from Streamlit secrets
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    agent = StudentAgent(openai_api_key)
    agent.run()