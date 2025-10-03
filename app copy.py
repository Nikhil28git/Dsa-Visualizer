from flask import Flask, request, render_template
import os
import docx2txt
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from sentence_transformers import SentenceTransformer, util
from werkzeug.utils import secure_filename

# Set up Tesseract OCR path (Windows example)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Change this if needed

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Utility Functions ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
    except Exception as e:
        print(f"[ERROR] PDF parsing failed: {e}")

    if not text.strip():
        try:
            images = convert_from_path(file_path)
            for image in images:
                text += pytesseract.image_to_string(image)
        except Exception as e:
            print(f"[ERROR] OCR fallback failed: {e}")

    return text

def extract_text_from_docx(file_path):
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        print(f"[ERROR] DOCX extraction failed: {e}")
        return ""

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"[ERROR] TXT extraction failed: {e}")
        return ""

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.endswith('.txt'):
        return extract_text_from_txt(file_path)
    else:
        return ""

# --- Routes ---

@app.route("/")
def index():
    return render_template('matchresume.html')

@app.route("/matcher", methods=["POST"])
def matcher():
    job_description = request.form['job_description']
    resume_files = request.files.getlist('resumes')

    if not job_description or not resume_files:
        return render_template('matchresume.html', message="Please upload resumes and enter a job description.")

    job_embedding = model.encode(job_description, convert_to_tensor=True)

    scores = []
    filenames = []

    for file in resume_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            text = extract_text(filepath)
            if not text.strip():
                print(f"[INFO] Skipped empty resume: {filename}")
                continue

            resume_embedding = model.encode(text, convert_to_tensor=True)
            similarity = util.cos_sim(job_embedding, resume_embedding).item()
            scores.append(round(similarity, 2))
            filenames.append(filename)
        else:
            print(f"[WARNING] Unsupported file skipped: {file.filename}")

    if not scores:
        return render_template('matchresume.html', message="No valid resumes could be processed.")

    top = sorted(zip(filenames, scores), key=lambda x: x[1], reverse=True)[:5]
    results = list(zip([t[0] for t in top], [t[1] for t in top]))

    return render_template('matchresume.html', message="Top Matching Resumes:", results=results)

# --- Run App ---
if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
