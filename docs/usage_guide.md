# StoryWriter Usage Guide

This guide will help you generate your own science fiction stories that incorporate fluid dynamics and oceanography concepts.

## Prerequisites

1. Install Python 3.7 or higher
2. Install the required dependencies:
   ```
   pip install requests pyyaml
   ```
3. Obtain a DeepSeek API key

## Configuration

1. Set your API key as an environment variable:
   ```
   export DEEPSEEK_API_KEY=your_api_key_here
   ```

2. Define your stories in `data/stories.yaml`:
   ```yaml
   new_stories:
     - name: "Your Story Title"
       keywords:
        - "Scientific concept 1"
        - "Scientific concept 2"
        - "Scientific concept 3"
        - "Scientific concept 4"
       description: "A brief description of your story plot"
   ```

## Generating Stories

Run the generator script from the project root directory:

```
python src/generate_stories.py
```

This will:
1. Process each story defined in your YAML file
2. Generate a plan and multiple story parts
3. Save output to the `story_output/` directory with individual part files and a combined full story

## Story Structure

Each generated story follows this structure:

1. **Part 1/5**: Introduction to characters and concepts
2. **Part 2/5**: Development and integration of scientific concepts 
3. **Intermission**: Real science explanation of concepts from parts 1-2
4. **Part 3/5**: Rising action and deeper exploration
5. **Part 4/5**: Climax incorporating scientific principles
6. **Part 5/5**: Resolution
7. **Science Recap**: Explanation of concepts from parts 3-5

## Customization

You can modify the following parameters in `src/generate_stories.py`:

- `n_parts`: Number of main story parts (default: 5)
- `MAX_TOKENS_PER_PART`: Maximum token length per part (default: 8150)
- `RATE_LIMIT_SEC`: Pause between API requests (default: 1 second)

## Example Output

See `examples/sample_output/Kvothe_and_the_Echo_Beings/` for a complete sample story.