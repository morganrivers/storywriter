import subprocess
import re
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright
import yaml
NODE_SCRIPT = 'src/math_to_speech.js'


def safe_slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")[:50]

def load_story_paths_from_yaml(yaml_path: Path) -> list[Path]:
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    paths = []
    for story in config["new_stories"]:
        slug = safe_slug(story["name"])
        path = Path("story_output") / slug / f"{slug}_full_story.txt"
        if not path.exists():
            print(f"⚠️ Warning: Missing story file for '{story['name']}': {path}")
            continue
        paths.append(path)
    return paths

def get_speech_from_latex(latex_expr):
    print("latex expr")
    print(latex_expr[2:-2])
    result = subprocess.run(
        ['node', NODE_SCRIPT],
        input=latex_expr[2:-2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError(f"SRE/Temml error:\n{result.stderr}")
    return "\n\n"+result.stdout.strip()+"\n\n"

def preprocess_text(raw_text: str, to_audio: bool) -> str:
    # Convert triple dashes into <hr>
    raw_text = re.sub(r"^\s*---\s*$", "<hr>", raw_text, flags=re.MULTILINE)

    def corrupt_equation(match):
        eq = match.group(1)
        spoken = get_speech_from_latex(eq)
        # corrupted = ''.join(c + '0' for c in eq)

        return f'<div>{spoken}</div>'
    if to_audio:
        raw_text = re.sub(r'(\\\[.*?\\\])', corrupt_equation, raw_text, flags=re.DOTALL)
        raw_text = re.sub(r'(\\\(.*?\\\))', corrupt_equation, raw_text, flags=re.DOTALL)
    # raw_text = re.sub(r'(\$\$.*?\$\$)', corrupt_equation, raw_text, flags=re.DOTALL)

    # # Protect display equations
    # raw_text = re.sub(r'(\$\$.*?\$\$)', r'<div>\1</div>', raw_text, flags=re.DOTALL)

    # Split into paragraphs
    paragraphs = raw_text.strip().split('\n\n')
    processed_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if para.startswith('<div>') and para.endswith('</div>'):
            # Keep raw MathJax block
            processed_paragraphs.append(para)
        else:
            # Replace single newlines in paragraph with <br>
            para = para.replace('\n', '<br>\n')
            processed_paragraphs.append(f"<p>{para}</p>")

    return "\n\n".join(processed_paragraphs)

# ----------- Markdown to HTML -----------

def markdown_to_html(md_text: str) -> str:
    return md_text
    # return markdown.markdown(
    #     md_text,
    #     extensions=['fenced_code', 'codehilite', 'toc', 'md_in_html']
    # )

# ----------- HTML Wrapper -----------

def generate_full_html(html_body: str) -> str:
    pre = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>MathJax 3 demo</title>
    <style>
      body {
        font-family: Georgia, serif;
        line-height: 1.6;
        margin: 2em auto;
        max-width: 700px;
        padding: 0 1em;
        color: #222;
      }
      h1, h2, h3 {
        margin-top: 1.5em;
      }
      p {
        margin-bottom: 1em;
      }
      ul, ol {
        padding-left: 1.5em;
        margin-bottom: 1em;
      }
      hr {
        margin: 2em 0;
        border: none;
        border-top: 1px solid #ccc;
      }
      pre {
        background: #f9f9f9;
        padding: 0.8em;
        overflow-x: auto;
      }
    </style>
    <!-- MathJax 3 configuration -->
    <script>
      window.MathJax = {
        tex: {
          inlineMath: [ ['$', '$'], ['\\\\(', '\\\\)']],
          displayMath: [ ['$$','$$'], ['\\\\[','\\\\]']]
        }
      };
    </script>
    <script async id="MathJax-script"
            src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js">
    </script>
  </head>

  <body>"""

    post = """
  </body>
</html>
"""

    mid = f"{html_body}"

    return pre + mid + post

# ----------- Render to PDF with Playwright -----------

def render_with_playwright(input_html, output_pdf):
    path = Path(input_html).resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        page.goto(path, wait_until="networkidle")
        page.evaluate("() => MathJax.startup.promise")
        page.pdf(path=output_pdf, format="A4", print_background=True)
        browser.close()

# ----------- Pipeline -----------
def main():
    story_paths = load_story_paths_from_yaml(Path("data/stories.yaml"))

    for txt_path in story_paths:
        raw_text = txt_path.read_text(encoding="utf-8")
        slug = txt_path.stem.replace("_full_story", "")

        html_path = txt_path.parent / f"{slug}.html"
        pdf_path  = txt_path.parent / f"{slug}.pdf"

        
        html_body = preprocess_text(raw_text,False)
        full_html = generate_full_html(html_body)
        html_path.write_text(full_html, encoding="utf-8")
        render_with_playwright(str(html_path), str(pdf_path))
        print(f"✅ Rendered: {pdf_path}")


        html_path = txt_path.parent / f"{slug}_audio.html"
        pdf_path  = txt_path.parent / f"{slug}_audio.pdf"

        html_body = preprocess_text(raw_text, to_audio=True)
        full_html = generate_full_html(html_body)
        html_path.write_text(full_html, encoding="utf-8")
        render_with_playwright(str(html_path), str(pdf_path))
        print(f"✅ Rendered: {pdf_path} with audio equations")


# def main():
#     txt_path = get_latest_story_txt(Path("stories.yaml"))
#     txt_path = Path("Kvothe_and_the_Echo_Beings_full_story.txt")
#     html_path = Path("kvothe_rendered.html")
#     pdf_path = Path("kvothe_rendered.pdf")

#     raw_text = txt_path.read_text(encoding="utf-8")
    
#     # preprocessed = preprocess_text(raw_text,False)
#     # html_body  = preprocessed
#     # # html_body = markdown_to_html(preprocessed)
#     # full_html = generate_full_html(html_body)
#     # html_path.write_text(full_html, encoding="utf-8")

#     # render_with_playwright(str(html_path), str(pdf_path))
#     # print(f"✅ Rendered: {pdf_path}")

#     html_path = Path("kvothe_rendered_audio.html")
#     pdf_path = Path("kvothe_rendered_audio.pdf")

#     preprocessed = preprocess_text(raw_text,True)
#     html_body  = preprocessed
#     # html_body = markdown_to_html(preprocessed)
#     full_html = generate_full_html(html_body)
#     html_path.write_text(full_html, encoding="utf-8")

#     render_with_playwright(str(html_path), str(pdf_path))
#     print(f"✅ Rendered: {pdf_path}")


if __name__ == "__main__":
    main()

