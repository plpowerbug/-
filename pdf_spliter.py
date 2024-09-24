from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_pdf, output_folder):
    pdf = PdfReader(input_pdf)
    for page_num in range(len(pdf.pages)):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf.pages[page_num])
        output_filename = f"{output_folder}/page_{page_num + 1}.pdf"
        with open(output_filename, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
        print(f'Created: {output_filename}')

# Example usage:
split_pdf(r"C:\Users\13915\payroll\split.pdf", "output_folder")