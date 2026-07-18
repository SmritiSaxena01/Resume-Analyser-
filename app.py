import os
import fitz  # PyMuPDF
from groq import Groq
from dotenv import load_dotenv
from PyPDF2 import PdfMerger
import gradio as gr

# Load environment variables (useful for local development)
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
# On Render, GROQ_API_KEY should be set in the environment variables settings
client = Groq(api_key=GROQ_API_KEY)

def get_path(file_obj):
    if file_obj is None:
        return None
    if hasattr(file_obj, 'name'):
        return file_obj.name
    return str(file_obj)

def extract_text(pdf_file_path):
    if not pdf_file_path:
        return ""
    document = fitz.open(pdf_file_path)
    text = ""
    for page in document:
        text += page.get_text()
    document.close()
    return text

def load_resume(pdf_file_path):
    text = extract_text(pdf_file_path)
    if len(text) < 100:
        return None
    return text

def create_prompt(resume_text):
    prompt = f"""
    You are an expert HR Recruiter and ATS Resume Analyzer 

    Analyze the following resume Carefully 

    Resume :

    {resume_text}

    Return your response in the following format 

    # ATS Score 
    (Give Score out of 100)
    # Resume Summary 

    # Technical Skills Found 

    # Strength 

    # Weakness

    # Missing Skills 

    # HR Feedback 
    keep the response professional and easy to understand    
    """
    return prompt

def analyze_resume(resume_text):
    prompt = create_prompt(resume_text)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content

def resume_statistics(text):
    stats = f"""
    Characters : {len(text)}

    WORDS : {len(text.split())}

    Lines :  {len(text.splitlines())}
    """
    return stats

def generate_complete_report(pdf_file_path):
    resume_text = load_resume(pdf_file_path)
    if resume_text is None:
        return "Not able to read or resume seems empty (less than 100 characters)."
    
    stats = resume_statistics(resume_text)
    report = analyze_resume(resume_text)
    return stats + "\n\n\n" + report

def analyze_upload_resume(pdf_file):
    if pdf_file is None:
        return "Please Upload a Resume"

    try:
        pdf_path = get_path(pdf_file)
        report = generate_complete_report(pdf_path)

        with open("history.txt", "a", encoding="utf-8") as file:
            file.write("\n")
            file.write("="*60)
            file.write("\n")
            file.write(report)
            file.write("\n")

        return report

    except Exception as e:
        return f"Error : {e}"

def generate_linkedin_post(pdf):
    if pdf is None:
        return "Please Upload a Resume"
        
    try:
        pdf_path = get_path(pdf)
        resume = extract_text(pdf_path)

        prompt = f"""
Create a professional LinkedIn post based on this resume.

{resume}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        linkedin_post = response.choices[0].message.content

        with open("linkedin_post.txt", "w", encoding="utf-8") as file:
            file.write(linkedin_post)

        return linkedin_post
    except Exception as e:
        return f"Error: {e}"

def merge_pdf(pdf1, pdf2):
    if pdf1 is None or pdf2 is None:
        return None
        
    try:
        merger = PdfMerger()
        merger.append(get_path(pdf1))
        merger.append(get_path(pdf2))

        output = "Merged_Notes.pdf"
        merger.write(output)
        merger.close()

        return output
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        return None

# Build Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as app:

    gr.Markdown("# 🤖 AI Resume Analyzer")

    # ---------- Resume Analyzer ----------
    with gr.Tab("Resume Analyzer"):
        resume_input = gr.File(label="Upload Resume", file_types=[".pdf"])
        output1 = gr.Textbox(label="Analysis", lines=15)
        analyze_btn = gr.Button("Analyze")
        analyze_btn.click(
            fn=analyze_upload_resume,
            inputs=resume_input,
            outputs=output1
        )

    # ---------- LinkedIn Post ----------
    with gr.Tab("LinkedIn Post"):
        resume2_input = gr.File(label="Upload Resume", file_types=[".pdf"])
        output2 = gr.Textbox(label="LinkedIn Post", lines=10)
        generate_btn = gr.Button("Generate")
        generate_btn.click(
            fn=generate_linkedin_post,
            inputs=resume2_input,
            outputs=output2
        )

    # ---------- Merge PDF ----------
    with gr.Tab("Merge PDF"):
        pdf1_input = gr.File(label="PDF 1", file_types=[".pdf"])
        pdf2_input = gr.File(label="PDF 2", file_types=[".pdf"])
        output3 = gr.File(label="Merged PDF")
        merge_btn = gr.Button("Merge")
        merge_btn.click(
            fn=merge_pdf,
            inputs=[pdf1_input, pdf2_input],
            outputs=output3
        )

if __name__ == "__main__":
    # Render sets PORT environment variable automatically
    port = int(os.environ.get("PORT", 7860))
    # Host 0.0.0.0 allows external routing on Render
    app.launch(server_name="0.0.0.0", server_port=port)
