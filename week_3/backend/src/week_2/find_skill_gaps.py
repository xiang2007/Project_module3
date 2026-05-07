import sqlite3
import re
from typing import List, Set
from pydantic import BaseModel
from dotenv import load_dotenv

# Configuration
load_dotenv()


class SkillGapResult(BaseModel):
    """Result model for skill gap analysis."""
    gaps: List[str]
    resume_skills: List[str]
    available_skills: List[str]


def extract_resume_skills(input_file_path: str) -> Set[str]:
    """
    Extract skills from resume file using deterministic regex parsing.
    Focuses on the SKILLS section of the resume.
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading resume file: {e}")
        return set()
    
    skills = set()
    
    # Extract SKILLS section using regex
    skills_section_match = re.search(
        r'SKILLS\s*\n(.*?)(?=\n[A-Z]+|\Z)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    
    if not skills_section_match:
        return skills
    
    skills_text = skills_section_match.group(1)
    
    # Extract Technical Skills
    tech_skills_match = re.search(
        r'Technical\s*Skills?\s*:?\s*([^\n]+)',
        skills_text,
        re.IGNORECASE
    )
    if tech_skills_match:
        tech_skills_str = tech_skills_match.group(1)
        # Split by comma and clean
        tech_skills = [s.strip().lower() for s in tech_skills_str.split(',')]
        skills.update(tech_skills)
    
    # Extract Languages
    languages_match = re.search(
        r'Languages?\s*:?\s*([^\n]+)',
        skills_text,
        re.IGNORECASE
    )
    if languages_match:
        languages_str = languages_match.group(1)
        languages = [s.strip().lower() for s in languages_str.split(',')]
        skills.update(languages)
    
    # Extract Additional Skills
    additional_match = re.search(
        r'Additional\s*Skills?\s*:?\s*([^\n]+)',
        skills_text,
        re.IGNORECASE
    )
    if additional_match:
        additional_str = additional_match.group(1)
        additional = [s.strip().lower() for s in additional_str.split(',')]
        skills.update(additional)
    
    return skills


def get_available_skills_from_db(db_url: str) -> Set[str]:
    """
    Query database for all available tech stacks and extract unique skills.
    Deterministically parses tech_stack column from tagged jobs.
    """
    available_skills = set()
    
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        
        # Fetch all tech_stack values
        cursor.execute("SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL AND tech_stack != ''")
        rows = cursor.fetchall()
        
        for row in rows:
            if row[0]:
                # Split by comma and clean each skill
                skills = [s.strip().lower() for s in row[0].split(',')]
                available_skills.update(skills)
        
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
    
    return available_skills


def normalize_skill(skill: str) -> str:
    """
    Normalize skill name for comparison (deterministic).
    Removes extra whitespace and converts to lowercase.
    """
    return re.sub(r'\s+', ' ', skill.strip().lower())


def find_matching_skills(resume_skills: Set[str], available_skills: Set[str]) -> Set[str]:
    """
    Find matching skills between resume and database using fuzzy matching logic.
    Uses normalized comparison for deterministic results.
    """
    matched = set()
    
    for resume_skill in resume_skills:
        normalized_resume = normalize_skill(resume_skill)
        
        for available_skill in available_skills:
            normalized_available = normalize_skill(available_skill)
            
            # Exact match
            if normalized_resume == normalized_available:
                matched.add(resume_skill)
                break
            
            # Substring match (if resume skill is in available skill)
            if normalized_resume in normalized_available or normalized_available in normalized_resume:
                matched.add(resume_skill)
                break
    
    return matched


def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
    """
    Identify skill gaps by comparing resume skills against available tech stacks in database.
    
    Args:
        input_file_path: Path to resume file
        db_url: Path to database file
    
    Returns:
        SkillGapResult with identified skill gaps
    """
    # Extract skills from resume
    resume_skills = extract_resume_skills(input_file_path)
    
    # Get available skills from database
    available_skills = get_available_skills_from_db(db_url)
    
    # Find matching skills
    matched_skills = find_matching_skills(resume_skills, available_skills)
    
    # Calculate gaps (skills in resume but not in database)
    gaps = sorted(list(resume_skills - matched_skills))
    
    # Prepare result
    result = SkillGapResult(
        gaps=gaps,
        resume_skills=sorted(list(resume_skills)),
        available_skills=sorted(list(available_skills))
    )
    
    return result


if __name__ == "__main__":
    # Example usage
    result = find_skill_gaps("data/resume_d3.txt", "data/jobs_d1.db")
    print(f"Skill Gaps: {result.gaps}")
    print(f"Resume Skills: {result.resume_skills}")
    print(f"Available Skills in DB: {result.available_skills[:10]}...")  # Show first 10
