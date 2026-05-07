import sqlite3
import os
import time
import google.genai as genai
from typing import List, Tuple
from dotenv import load_dotenv

# Configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BATCH_SIZE = 5  # Justifiable size to stay within rate limits
RETRY_DELAY = 2  # Seconds to wait if an API error occurs

client = genai.Client(api_key=GEMINI_API_KEY)

# Global tracking for tokens and timing
total_tokens_used = 0
start_time = None

def get_tech_stack_batch(descriptions: List[str]) -> List[str]:
    """Sends a batch of descriptions to Gemini and returns a list of tech stacks."""
    global total_tokens_used
    
    # We ask for a specific format to make parsing easy
    combined_prompt = "Extract the tech stack from each job description below. " \
                      "Return ONLY the tech stacks, one per line, without any 'Job N:' prefix. " \
                      "Format: Tech1, Tech2, Tech3\n\n"

    for i, desc in enumerate(descriptions):
        combined_prompt += f"Job {i+1}: {desc}\n---\n"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=combined_prompt
        )
        # Track token usage if available
        if hasattr(response, "usage_metadata"):
            total_tokens_used += response.usage_metadata.total_token_count
        
        # Split response by lines and clean up
        text = getattr(response, "text", None) or str(response)
        stacks = []
        for line in text.strip().split('\n'):
            line = line.strip()
            # Skip empty lines and any lines that are just labels
            if line and line.lower() not in ['job', '---']:
                stacks.append(line)
        return stacks
    except Exception as e:
        # Graceful error handling: log then return empty strings for each description
        print(f"Error calling generative model: {e}")
        return [""] * len(descriptions)


def tag_data(db_url: str):
    """
    Tags job descriptions with their tech stacks using Gemini API.
    Reads from jobs table and populates tech_stack column for rows without values.
    """
    global total_tokens_used, start_time
    
    start_time = time.time() * 1000  # Convert to milliseconds
    conn = None
    data_tagged = False
    
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()

        batch_attempt = 0
        while True:
            # 1. Fetch a batch of jobs where tech_stack is empty
            cursor.execute(
                "SELECT source_id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = '' LIMIT ?",
                (BATCH_SIZE,)
            )
            rows = cursor.fetchall()

            if not rows:
                break  # All jobs processed

            data_tagged = True
            ids = [row[0] for row in rows]
            descriptions = [row[1] for row in rows]

            # 2. Extract tech stacks via Gemini
            tech_stacks = get_tech_stack_batch(descriptions)

            # 3. Handle Batch Size Mismatch (Constraint validation)
            if len(tech_stacks) != len(ids):
                batch_attempt += 1
                print(f"[Batch {batch_attempt}] Attempt 1 failed: Mismatch between batch size and response")
                time.sleep(RETRY_DELAY)
                continue

            # 4. Batch Update the database
            updates = []
            for i in range(len(ids)):
                updates.append((tech_stacks[i], ids[i]))
                # Log to standard output as required
                print(f"Analyzed Job {ids[i]}: {tech_stacks[i]}")

            cursor.executemany("UPDATE jobs SET tech_stack = ? WHERE source_id = ?", updates)
            conn.commit()
            batch_attempt += 1

            # Rate limiting safety
            time.sleep(1)

        # Print final status
        if not data_tagged:
            print("No data to tag")

    except Exception as e:
        # Handle all errors gracefully without crashing
        print(f"Error in tag_data: {e}")
    finally:
        if conn:
            conn.close()
        
        # Print timing and token stats
        end_time = time.time() * 1000
        elapsed_ms = end_time - start_time
        print(f"Total tokens used: {total_tokens_used}, took {elapsed_ms:.3f}ms")


if __name__ == "__main__":
    # Example usage for 'uv run tag_data.py'
    tag_data("data/jobs_d1.db")
