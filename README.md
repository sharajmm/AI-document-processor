# 🤖 AI-Powered Document Processing Pipeline

A complete AI-powered document processing system that automatically extracts, classifies, and structures information from uploaded documents (PDFs, images, scanned forms) using OCR and AI processing.

## ✨ Features

- 📤 **Document Upload**: Support for PDF, JPG, PNG files via intuitive Streamlit UI
- 👁️ **OCR Processing**: Text extraction using Tesseract or EasyOCR with preprocessing
- 🤖 **AI Analysis**: Document classification, field extraction, and summarization via OpenRouter API
- 💾 **Dual Storage**: Original documents in GitHub, structured data in SQLite/Supabase
- 🔍 **Smart Search**: Search and filter documents by content, type, date, and fields
- 📊 **Data Export**: Export processed data to CSV/Excel formats
- 📈 **Analytics**: Real-time statistics and document type breakdowns

## 🏗️ Architecture

```
User Upload → OCR Processing → AI Analysis → Database Storage → GitHub Storage → Search/Export
```

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **OCR**: Tesseract OCR / EasyOCR + OpenCV preprocessing
- **AI Processing**: OpenRouter API (mistralai/mistral-small-3.2-24b-instruct:free)
- **Database**: SQLite (default) / Supabase (optional)
- **Storage**: GitHub API for original documents
- **Export**: Pandas → CSV/Excel

## 📋 Prerequisites

### System Dependencies

1. **Tesseract OCR** (required for OCR functionality)

   - **Windows**: Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`

2. **Python 3.8+**

### API Keys & Services

- **OpenRouter API Key**: Get free tier at [OpenRouter.ai](https://openrouter.ai/)
- **GitHub Personal Access Token**: Create at GitHub Settings → Developer settings → Personal access tokens
- **GitHub Repository**: Create a public/private repo for document storage

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd ai-document-processor

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your actual values (see Configuration section below)
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## ⚙️ Configuration

### Required Environment Variables (.env file)

```env
# 🚨 REPLACE WITH YOUR ACTUAL VALUES 🚨

# OpenRouter API Configuration
OPENROUTER_API_KEY=your_actual_openrouter_api_key_here

# GitHub Configuration for Document Storage
GITHUB_TOKEN=your_actual_github_personal_access_token_here
GITHUB_REPO=yourusername/your-repo-name

# Database Configuration (SQLite by default)
DB_URL=sqlite:///documents.db
# For Supabase: DB_URL=postgresql://username:password@host:port/database

# OCR Engine (tesseract or easyocr)
OCR_ENGINE=tesseract

# AI Model Configuration
AI_MODEL=mistralai/mistral-small-3.2-24b-instruct:free

# Upload Limits
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png
```

## 🔧 Manual Configuration Steps

### 1. OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to `OPENROUTER_API_KEY` in `.env`

### 2. GitHub Configuration

1. **Create GitHub Personal Access Token:**

   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Generate new token (classic)
   - Select scopes: `repo` (for private repos) or `public_repo` (for public repos)
   - Copy token to `GITHUB_TOKEN` in `.env`

2. **Create Document Storage Repository:**
   - Create a new GitHub repository (e.g., `my-docs-storage`)
   - Set `GITHUB_REPO=yourusername/my-docs-storage` in `.env`

### 3. Tesseract Installation

- **Windows**: Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 4. Optional: Supabase Database

If you prefer Supabase over SQLite:

1. Create account at [Supabase.com](https://supabase.com)
2. Create new project
3. Get database URL from Settings → Database
4. Update `DB_URL` in `.env`

## 📁 Project Structure

```
ai-document-processor/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration management
├── ocr_utils.py          # OCR processing functions
├── ai_utils.py           # AI/OpenRouter integration
├── db_utils.py           # Database models and operations
├── github_utils.py       # GitHub API integration
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## 💡 Usage Guide

### 1. Upload Documents

- Navigate to "Upload" tab
- Drag & drop or select PDF/image files
- Click "Process Documents"
- Monitor processing status

### 2. Search & Browse

- Use "Search" tab to find documents
- Filter by document type, date range, or keywords
- View extracted fields and summaries
- Download original files from GitHub

### 3. Export Data

- Go to "Export" tab
- Choose CSV or Excel format
- Optionally include extracted text
- Download structured data

### 4. View Statistics

- Check "Stats" tab for analytics
- Monitor document types breakdown
- Track recent activity

## 🔍 OCR Preprocessing Features

The system includes advanced OCR preprocessing for better accuracy:

- **Deskewing**: Corrects rotated text
- **Binarization**: Converts to optimal black/white contrast
- **Noise Reduction**: Removes artifacts and noise
- **Gaussian Blur**: Smooths text edges

## 🤖 AI Processing Capabilities

The AI extracts and analyzes:

- **Document Classification**: Invoice, receipt, contract, letter, form, other
- **Field Extraction**: Names, dates, amounts, addresses, phone numbers, emails
- **Content Summarization**: 2-3 sentence summaries
- **Confidence Scoring**: Reliability assessment
- **Metadata**: Language detection, word count estimation

## 🚨 Troubleshooting

### Common Issues

1. **"Configuration Error" on startup**

   - Check all variables in `.env` file are set
   - Ensure no spaces around `=` in `.env`

2. **"Tesseract not found" error**

   - Install Tesseract OCR system dependency
   - On Windows, add Tesseract to PATH

3. **"GitHub access issues"**

   - Verify GitHub token has correct permissions
   - Check repository exists and is accessible
   - Ensure token hasn't expired

4. **"OpenRouter API failed"**

   - Verify API key is valid
   - Check you have available credits/quota
   - Ensure internet connection is stable

5. **Database errors**
   - For SQLite: ensure write permissions in app directory
   - For Supabase: verify connection URL and credentials

### Performance Tips

- **Large PDFs**: Consider splitting into smaller files
- **Batch Processing**: Upload files in smaller batches for better performance
- **OCR Quality**: Use high-resolution images (300+ DPI) for best results
- **Network**: Stable internet connection required for AI processing

## 🔒 Security Notes

- Keep your `.env` file secure and never commit it to version control
- Regularly rotate your API keys and tokens
- Consider using private GitHub repositories for sensitive documents
- Monitor your OpenRouter API usage to avoid unexpected charges

## 🆙 Future Enhancements

Potential improvements:

- Multi-language OCR support
- Custom AI model fine-tuning
- Advanced document templates
- Webhook integrations
- REST API endpoints
- Docker containerization

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review configuration steps
3. Open an issue on GitHub
4. Check OpenRouter and GitHub documentation

---

**Made with ❤️ using Streamlit, OpenRouter AI, and open-source tools**
