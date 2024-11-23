from pathlib import Path
import json
import os
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
import numpy as np
from openai import OpenAI

@dataclass
class StudentProfile:
    interests: List[str]
    skills: List[str]
    courses: List[Dict[str, str]]  # [{name: grade}]
    preferred_topics: List[str]
    cv_summary: str
    gpa: float

@dataclass
class ThesisProject:
    title: str
    description: str
    research_fields: List[str]
    technical_requirements: Dict[str, List[str]]
    chair_name: str
    source_url: str

def parse_chair_data(content: str) -> tuple[dict, list]:
    """
    Parse chair data and thesis opportunities from aggregated text file.
    Returns (chair_info, thesis_opportunities)
    """
    # Split into chair info and thesis opportunities
    sections = content.split("THESIS OPPORTUNITIES:")
    print('>>>>> ',len(sections))
    if len(sections) != 2:
        raise ValueError("Invalid format: Could not find THESIS OPPORTUNITIES section")
    
    chair_section = sections[0].strip()
    opportunities_section = sections[1].strip()
    
    # Parse chair information
    chair_info = {}
    for line in chair_section.split('\n'):
        if line.startswith('- '):
            parts = line[2:].split(': ', 1)
            if len(parts) == 2:
                key, value = parts
                # Clean up markdown links if present
                if '[' in value and ']' in value:
                    value = value.split('](')[0].strip('[]')
                chair_info[key.strip()] = value.strip()
    
    # Parse research areas into list
    if 'Research Areas' in chair_info:
        chair_info['Research Areas'] = [
            area.strip() 
            for area in chair_info['Research Areas'].split(',')
        ]
    
    # Parse thesis opportunities
    opportunities = []
    current_opportunity = None
    
    for line in opportunities_section.split('\n'):
        line = line.strip()
        if not line or line.startswith('Note:'):
            continue
            
        if line.startswith('**Opportunity'):
            if current_opportunity:
                opportunities.append(current_opportunity)
            current_opportunity = {
                'chair_name': chair_info.get('Chair/Department Name', ''),
                'chair_contact': chair_info.get('General Contact', ''),
                'chair_website': chair_info.get('Website', ''),
                'chair_research_areas': chair_info.get('Research Areas', [])
            }
        elif current_opportunity is not None and line.startswith('- '):
            parts = line[2:].split(': ', 1)
            if len(parts) == 2:
                key, value = parts
                # Handle special fields
                if key == 'Research Fields' and value != 'Not provided':
                    value = [field.strip() for field in value.split(',')]
                elif value in ['Not provided', 'Not explicitly mentioned']:
                    value = None
                current_opportunity[key.strip()] = value
    
    # Add the last opportunity
    if current_opportunity:
        opportunities.append(current_opportunity)
    
    # Clean up opportunities
    for opp in opportunities:
        # Ensure all required fields exist
        required_fields = [
            'Type', 'Title', 'Description', 'URL', 'Contact Person',
            'Research Fields', 'Technical Requirements', 'Academic Requirements',
            'Timeline', 'Additional Information'
        ]
        for field in required_fields:
            if field not in opp:
                opp[field] = None
    
    return chair_info, opportunities


class ThesisMatchingAgent:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.output_dir = Path("matching_results")
        self.output_dir.mkdir(exist_ok=True)


    def load_student_data(self, student_dir: Path) -> Dict:
        """
        Load student data from the directory containing:
        - student_data.json
        - cv_summary.txt
        - transcript_summary.txt
        """
        try:
            # Load the JSON data
            with open(student_dir / "student_data.json", "r", encoding='utf-8') as f:
                student_data = json.load(f)
            
            # Load CV summary
            with open(student_dir / "cv_summary.txt", "r", encoding='utf-8') as f:
                cv_summary = f.read().strip()
                
            # Load transcript summary
            with open(student_dir / "transcript_summary.txt", "r", encoding='utf-8') as f:
                transcript_summary = f.read().strip()
            
            # Combine all data
            student_profile = {
                # Core information
                "cv_summary": cv_summary,
                "transcript_summary": transcript_summary,
                
                # From JSON file
                "interests": student_data.get("interests", []),
                "preferred_topics": student_data.get("preferred_topics", []),
                "skills": student_data.get("skills", []),
                "gpa": student_data.get("gpa", "Not available"),
                "courses": student_data.get("courses", []),
                
                # Additional data if available
                "personal_info": student_data.get("personal_info", {}),
                "motivation_letter_text": student_data.get("motivation_letter_text", None),
            }
            
            # Add key areas of study if available in transcript summary
            if "Key Areas of Study:" in transcript_summary:
                areas = transcript_summary.split("Key Areas of Study:")[1].strip()
                student_profile["key_areas"] = [
                    area.strip("- ") 
                    for area in areas.split("\n") 
                    if area.strip().startswith("-")
                ]
            
            return student_profile
            
        except FileNotFoundError as e:
            raise Exception(f"Missing required student file: {e.filename}")
        except json.JSONDecodeError:
            raise Exception("Invalid student_data.json file")
        except Exception as e:
            raise Exception(f"Error loading student data: {str(e)}")
        

    def load_thesis_data(self, thesis_data_dir: Path) -> List[Dict]:
        """Load all thesis opportunities from the chair files"""
        all_projects = []
        
        # Process each chair file
        for file_path in thesis_data_dir.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                print('>>>>> ',file_path)
                content = f.read()
                
            chair_info, projects = parse_chair_data(content)
            all_projects.extend(projects)
            
        return all_projects

    def analyze_match(self, student: StudentProfile, project: Dict) -> Dict:
        """Analyze how well a student matches a thesis project"""
        prompt = f"""Analyze how well this student matches the thesis project. Consider all aspects carefully.

                    STUDENT PROFILE:
                    CV Summary: {student['cv_summary']}

                    Academic Performance:
                    {student['transcript_summary']}

                    Interests: {', '.join(student['interests'])}
                    Preferred Topics: {', '.join(student['preferred_topics'])}
                    Skills: {', '.join(student['skills'])}
                    GPA: {student['gpa']}

                    THESIS PROJECT:
                    Title: {project['Title']}
                    Type: {project['Type']}
                    Chair: {project['chair_name']}
                    Description: {project['Description']}
                    Research Fields: {', '.join(project['Research Fields'])}
                    Technical Requirements: {project.get('Rechnical Requirements', 'Not specified')}
                    Academic Requirements: {project.get('Academic Requirements', 'Not specified')}
                    Contact: {project.get('contact_person', project['chair_contact'])}

                    Provide a detailed analysis with the following structure:

                    1. Match Score (0-100):

                    2. Key Strengths:
                    - List the student's strongest matching points
                    - Highlight relevant courses and grades
                    - Note matching skills and interests

                    3. Potential Gaps:
                    - Identify missing requirements
                    - Note areas needing improvement
                    - Suggest preparation steps

                    4. Recommendations:
                    - Specific actions to improve match
                    - Suggested preparation
                    - Points to emphasize in application

                    5. Detailed Analysis:
                    - Academic alignment
                    - Technical preparation
                    - Research interest fit
                    - Experience relevance

                    Be specific and reference actual courses, skills, and experiences from the student's profile.
                    """
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at matching students with thesis projects."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "analysis": response.choices[0].message.content,
            "thesis": project,
            "score": self.extract_score(response.choices[0].message.content)
        }

    def extract_score(self, analysis: str) -> int:
        """Extract numerical score from analysis text"""
        try:
            score_line = [line for line in analysis.split('\n') if "Score" in line][0]
            return int(''.join(filter(str.isdigit, score_line)))
        except:
            return 0

    def rank_matches(self, matches: List[Dict]) -> List[Dict]:
        """Rank matches by score and add rankings"""
        ranked = sorted(matches, key=lambda x: x['score'], reverse=True)
        for i, match in enumerate(ranked):
            match['rank'] = i + 1
        return ranked

    def generate_report(self, student: StudentProfile, matches: List[Dict]) -> str:
        """Generate a comprehensive matching report"""
        
        report = f"""THESIS MATCHING REPORT
                Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

                STUDENT PROFILE SUMMARY
                ----------------------
                Interests: {', '.join(student['interests'])}
                Skills: {', '.join(student['skills'])}
                Preferred Topics: {', '.join(student['preferred_topics'])}

                TOP THESIS MATCHES
                -----------------

                """
        # Add top 5 matches with details
        for match in matches[:5]:
            report += f"\n{match['rank']}. {match['thesis']['Title']} ({match['score']}% Match)\n"
            report += f"Chair: {match['thesis']['chair_name']}\n"
            report += f"URL: {match['thesis']['URL']}\n"
            report += f"\nAnalysis:\n{match['analysis']}\n"
            report += "-" * 80 + "\n"

        return report

    def run_matching(self, student_dir: Path, thesis_data_dir: Path) -> None:
        """Main matching process"""
        
        # Load data
        student = self.load_student_data(student_dir)
        print('>>>>> going to load thesis data')
        projects = self.load_thesis_data(thesis_data_dir)
        print('>>>>> ',len(projects))

        #return student, projects
        
        print(f"Analyzing {len(projects)} thesis opportunities...")
        #return student, projects
        # Analyze matches
        matches = []
        for project in projects:
            print(f"-- Analyzing match with {project['Title']}...")
            match = self.analyze_match(student, project)
            matches.append(match)
            print(f"-----> Matched with {project['Title']} ({match['score']}%)")
            #break

        #print(matches[0])
        #return matches
        
        # Rank matches
        ranked_matches = self.rank_matches(matches)
        
        # Generate report
        report = self.generate_report(student, ranked_matches)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"matching_report_{timestamp}.txt"
        
        with open(output_file, "w") as f:
            f.write(report)
            
        print(f"\nMatching analysis completed! Report saved to: {output_file}")
        return output_file