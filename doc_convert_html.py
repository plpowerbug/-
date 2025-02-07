import zipfile
import os

def extract_images_from_docx(docx_path, output_folder):
    with zipfile.ZipFile(docx_path, "r") as zip_ref:
        for file in zip_ref.namelist():
            if file.startswith("word/media/") and file.endswith((".png", ".jpg", ".jpeg", ".gif")):
                zip_ref.extract(file, output_folder)
                print(f"提取图片: {file}")

extract_images_from_docx("21012025 Achieva CRM User Manual.docx", "extracted_images")
