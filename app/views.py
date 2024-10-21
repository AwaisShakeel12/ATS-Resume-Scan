from django.shortcuts import render
from .llm_model import get_gemini_response, create_resume_fun

from .prompts import score_prompt, full_review, keyword_prompt, spell_prompt, improvement, resume_prompt
  
import os 
from PIL import Image


import pdf2image
import io
import base64


import google.generativeai as genai
from fpdf import FPDF


genai.configure(api_key='')
model = genai.GenerativeModel('gemini-1.5-flash')
poppler_path =r'C:\Users\Awais Shakeel\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin'



def newhome(request):
    return render(request, 'app/home2.html')






def input_pdf_setup(upload_file):
    if upload_file is not None:
        # Convert PDF to image
        images = pdf2image.convert_from_bytes(upload_file.read(), poppler_path=poppler_path)
        first_page = images[0]
        
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                'mime_type': 'image/jpeg',
                'data': base64.b64encode(img_byte_arr).decode()
            }
        ]    
        return pdf_parts
    else:
        raise FileNotFoundError('No file uploaded')





def home(request):
    
    if request.method == 'POST':
        input_text = request.POST['input_text']
        upload_file = request.FILES.get('upload_file')
        
        if 'button' in request.POST:
            if request.POST['button'] == 'review':
                pdf_content = input_pdf_setup(upload_file)
                score = get_gemini_response(input_text, pdf_content, score_prompt)
                review = get_gemini_response(input_text, pdf_content, full_review) 
 
                return render(request , 'app/home2.html',{'score':score, 'review':review})

            elif request.POST['button'] == 'missing_keyword':
                pdf_content = input_pdf_setup(upload_file)
                response = get_gemini_response(input_text, pdf_content, keyword_prompt)
                
                return render(request , 'app/home2.html', {'response':response})
            
            elif request.POST['button'] == 'spelling':
                pdf_content = input_pdf_setup(upload_file)
                response = get_gemini_response(input_text, pdf_content, spell_prompt)
              
                return render(request , 'app/home2.html', {'response':response})
            
            elif request.POST['button'] == 'improvment':
                pdf_content = input_pdf_setup(upload_file)
                response = get_gemini_response(input_text, pdf_content, improvement)
                # cleaned_response = clean_response(response)
                return render(request , 'app/home2.html', {'response':response})
 
        
    return render(request , 'app/home2.html')




from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            # First header: Name and Role
            self.set_font('Arial', 'B', 12)
            self.cell(0, 8, f"{self.name} | {self.role}", 0, 1, 'C')

            # Second header: Email, Phone, Address
            self.set_font('Arial', '', 10)
            self.cell(0, 8, f"{self.email} | {self.phone} | {self.address}", 0, 1, 'C')

            # Third header: LinkedIn, Portfolio (if provided)
            if self.linkedin or self.portfolio:
                self.cell(0, 8, f"{self.linkedin} | {self.portfolio}", 0, 1, 'C')
            self.ln(5)  # Line space after header

    def section_title(self, title):
        # Bold for section titles only, such as Summary, Education, etc.
        self.set_font('Arial', 'B', 10)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(1)  # Reduced space after the title

    def section_body(self, body):
        # Regular text for section descriptions
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 5, body)
        self.ln(1)  # Reduced space after body

    def footer(self):
        # Add page number
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


# PDF Generation Function

def create_resume_pdf(generated_text, name, role, email, phone, address, linkedin, portfolio, filename=None):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    
    # Assigning header details to the PDF object
    pdf.name = name
    pdf.email = email
    pdf.phone = phone
    pdf.address = address
    pdf.linkedin = linkedin
    pdf.portfolio = portfolio
    pdf.role = role

    pdf.add_page()

    # Split text into sections based on provided formatting
    sections = generated_text.split("\n\n")
    
    for section in sections:
        if "\n" in section:
            title, body = section.split("\n", 1)
        else:
            title = section
            body = ""
        
        # Skip if title matches the header (name and role)
        if title.strip() == f"{name} | {role}":
            continue  # Skip this iteration to avoid repetition

        # Only make section titles bold (like Summary, Education, etc.)
        if title.strip().lower() in ['summary', 'education', 'experience', 'skills', 'projects', 'certificates']:
            pdf.section_title(title.strip())  # Bold title
            pdf.section_body(body.strip())  # Regular body text
        else:
            pdf.section_body(title.strip())  # Handle cases without body descriptions

    
    if not filename:
        filename = f"{name.replace(' ', '_').lower()}_resume.pdf"

    # Save the PDF to the specified filename
    pdf.output(filename)
    print(f"PDF generated: {filename}")


# View function for Django
def create_resume(request):
    if request.method == 'POST':
        name = request.POST['name']
        role = request.POST['role']
        experience = request.POST['experience']
        education = request.POST['education']
        skills = request.POST['skills']
        projects = request.POST['projects']
        certificates = request.POST['certificates']
        email = request.POST['email']
        phone = request.POST['phone']
        linkedin = request.POST['linkedin']
        portfolio = request.POST['portfolio']
        address = request.POST['address']

        # Combine input text into a single input string
        input_text = (
            f"Summary\n{role}\n\nEducation\n{education}\n\nExperience\n{experience}\n\n"
            f"Skills\n{skills}\n\nProjects\n{projects}\n\nCertificates\n{certificates}"
        )

        # Generate resume text from prompt
        result = create_resume_fun(input_text, resume_prompt)
        generated_text = result

        # Generate PDF
        pdf_filename = None  # Let the PDF function decide the filename based on the user's name
        create_resume_pdf(generated_text, name, role, email, phone, address, linkedin, portfolio, pdf_filename)

        return render(request, 'app/create_resume.html', {'generated_text': generated_text})

    return render(request, 'app/create_resume.html')
