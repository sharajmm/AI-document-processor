import cv2
import numpy as np
import pytesseract
import easyocr
from PIL import Image
import io
import PyPDF2
from pdf2image import convert_from_bytes
from config import Config

class OCRProcessor:
    def __init__(self):
        self.config = Config()
        # Add Tamil ('ta') support for EasyOCR
        if self.config.OCR_ENGINE == 'easyocr':
            self.easyocr_reader = easyocr.Reader(['en', 'ta'])
    
    def preprocess_image(self, image):
        """
        Preprocess image to improve OCR accuracy
        - Convert to grayscale
        - Apply Gaussian blur
        - Apply adaptive thresholding
        - Deskew if needed
        """
        # Convert PIL Image to OpenCV format
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding for better binarization
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Deskew the image
        deskewed = self._deskew_image(thresh)
        
        # Denoise
        denoised = cv2.medianBlur(deskewed, 3)
        
        return denoised
    
    def _deskew_image(self, image):
        """Correct skew in the image"""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        if abs(angle) > 0.5:  # Only deskew if angle is significant
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
        
        return image
    
    def extract_text_from_image(self, image_file):
        """Extract text from image file using OCR"""
        try:
            # Open image
            image = Image.open(image_file)

            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Extract text based on configured OCR engine
            if self.config.OCR_ENGINE == 'easyocr':
                results = self.easyocr_reader.readtext(processed_image)
                text = ' '.join([result[1] for result in results])
            else:  # Default to Tesseract
                # Add Tamil language support for Tesseract
                text = pytesseract.image_to_string(processed_image, lang='eng+tam')

            return text.strip()

        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        try:
            text = ""
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)  # Reset file pointer

            # Try to extract text directly first (for text-based PDFs)
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += page_text + "\n"
            except Exception:
                pass

            # If no text extracted or very little text, use OCR on PDF images
            if len(text.strip()) < 50:
                try:
                    # Convert PDF pages to images
                    images = convert_from_bytes(pdf_bytes, dpi=200)

                    for image in images:
                        # Preprocess and extract text from each page
                        processed_image = self.preprocess_image(image)

                        if self.config.OCR_ENGINE == 'easyocr':
                            results = self.easyocr_reader.readtext(processed_image)
                            page_text = ' '.join([result[1] for result in results])
                        else:
                            # Add Tamil language support for Tesseract
                            page_text = pytesseract.image_to_string(processed_image, lang='eng+tam')

                        text += page_text + "\n"

                except Exception as e:
                    raise Exception(f"Error processing PDF with OCR: {str(e)}")

            return text.strip()

        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def process_document(self, file):
        """Process document and extract text based on file type"""
        filename = file.name.lower()
        
        if filename.endswith('.pdf'):
            return self.extract_text_from_pdf(file)
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            return self.extract_text_from_image(file)
        else:
            raise ValueError(f"Unsupported file type: {filename}")

def get_ocr_processor():
    """Factory function to get OCR processor instance"""
    return OCRProcessor()
