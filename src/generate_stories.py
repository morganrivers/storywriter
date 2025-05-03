import pprint
import os
import time
import requests
from pathlib import Path
import yaml
def get_file_variables(yaml_file):
    with open(yaml_file, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # ensure you export this var
BASE_URL = "https://api.deepseek.com/v1/chat/completions"  # Changed to chat/completions
RATE_LIMIT_SEC = 1  # pause between requests
OUTPUT_BASE_DIR = Path("story_output")
OUTPUT_BASE_DIR.mkdir(exist_ok=True)

EXAMPLE_FILE = Path("examples/example_story.txt")
ALL_FLASHCARDS_FILE = Path("data/all_flashcards.txt")
# Increase from 4 to 8 parts, or set to 4 and increase token length
n_parts = 5
parts = [f"the plan for the story, for parts 1 through {n_parts}.", f"1/{n_parts}",f"2/{n_parts}","Intermission (Real science in parts 1 and 2)",f"3/{n_parts}",f"4/{n_parts}",f"5/{n_parts}","Recap: Real science in parts 3, 4, and 5"]  # Change to 4 if you want fewer, longer parts
MAX_TOKENS_PER_PART = 8150  # Adjust this for longer outputs per part

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def load_file(path: Path) -> str:
    """Read and return the contents of a file."""
    return path.read_text(encoding="utf-8").strip()

def call_deepseek(prompt: str) -> str:
    """
    Send a prompt to Deepseek and return the generated text.
    Raises for HTTP errors (e.g. 401 if your key is invalid).
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the environment.")
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    # Fixed payload structure for chat/completions endpoint
    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": 
             "You an expert short story author with a deep knowledge of oceanic and fluid dynamics. Create a cohesive narrative that teaches the audience the content from the provided flashcards."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": MAX_TOKENS_PER_PART,
        "temperature": 0.7,
    }
    
    try:
        resp = requests.post(BASE_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # For chat/completions, the response format is different
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        try:
            # Try to get more details about the error
            error_detail = resp.json()
            print(f"Error details: {error_detail}")
        except:
            print(f"Response text: {resp.text}")
        raise

def safe_slug(text: str) -> str:
    """Generate a filesystem-safe slug from a string."""
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")[:50]

# ------------------------------------------------------------------
# STORY GENERATION
# ------------------------------------------------------------------
def build_story( title: str, flashcards: str, description: str, example_story: str, all_flashcards: str):
    """Generate parts of a story based on provided metadata."""
    # Add specific instructions about how to use the flashcards
    instruction = (
        "I would like you to write a story for me. Each part of the story includes content\n "
        "from 2-4 of the flashcards and is approximately 1000 words. \n"
        f"Here is part 1/{n_parts}, 2/{n_parts}, and the intermission in an example story:\n"
        f"{example_story}\n\n"
        f"Relevant flashcards for your story are among the following:\n"
        f"{all_flashcards}\n\n"
    )
    
    metadata = (
        f"In particular, I would like you to choose 2-4 of these flashcards from the following list in each section of"
        f" the story, such that you end up covering them all by part {n_parts}/{n_parts} of the story.\n"
        f"The list of cards that must be covered by the end of part 5/5: {flashcards}\n"
        f"The title of your story is: {title}\n"
        f"Story Description: {description}\n"
    )

    slug = safe_slug(title)
    story_dir = OUTPUT_BASE_DIR / slug
    story_dir.mkdir(parents=True, exist_ok=True)

    conversation = []
    for i in range(len(parts)):
        part = parts[i]
        history = "\n".join(conversation)
        if i==0:
            what_to_generate = f"Please generate {part}\n"
        else:
            what_to_generate = f"Please generate this part of the story: {part}\n"
        prompt = (
            f"{instruction}\n"
            f"{metadata}\n"
            f"{history}\n"
            f"{what_to_generate}"
            f"Make your response approximately 1000 words long.\n"
            f" DO NOT mention bioluminescence in the story.\n"
            f" DO NOT have some surprise moment in"
            f" the story where something is revealed to be sentient.\n"
        )

        print(f"▶️ Generating '{title}' — part {part}...")
        print("")
        print("prompt")
        pprint.pprint(prompt)
        print("")
        output = call_deepseek(prompt)
        # output = "[PLACEHOLDER]"

        # Save this part
        part_file = story_dir / f"{slug}_part_{i}.txt"
        part_file.write_text(output, encoding="utf-8")
        conversation.append(f"Part: {part}:\n{output}")
        time.sleep(RATE_LIMIT_SEC)

    # Combine full story (should skip part 0)
    full_text = "\n\n".join(
        (story_dir / f"{slug}_part_{i}.txt").read_text(encoding="utf-8")
        for i in range(1, len(parts))
    )
    (story_dir / f"{slug}_full_story.txt").write_text(full_text, encoding="utf-8")
    print(f"✅ Completed story '{title}'. Files are in {story_dir}/")

# ------------------------------------------------------------------
# MAIN WORKFLOW
# ------------------------------------------------------------------
def main():
    example_story = load_file(EXAMPLE_FILE)
    all_flashcards = load_file(ALL_FLASHCARDS_FILE)
    yaml_file = "data/stories.yaml"
    variables = get_file_variables(yaml_file)

    for story in variables['new_stories']:
        title       = story['name']
        # join the keywords into whatever format your build_story expects
        flashcards  = ", ".join(story['keywords'])
        # description may come in as a list of strings
        if isinstance(story['description'], list):
            print("issue wiht description...")
            quit()
        else:
            # print("len(description)")
            # print(len(description))
            description = story['description']

        build_story(
            title,
            flashcards,
            description,
            example_story,
            all_flashcards
        )

if __name__ == "__main__":
    main()