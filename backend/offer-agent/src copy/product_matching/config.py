"""
Configuration file for HVAC Offer Request Product Name Extractor
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env files
# Load root .env first (for production/main config)
import pathlib
root_env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=root_env_path)

# Then load local .env (for local overrides)
load_dotenv()

class Config:
    """Configuration class for the HVAC offer extraction system"""
    
    # API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Mistral API Configuration (optional - for OCR fallback)
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')  # Optional for OCR fallback
    
    # File Paths
    PST_FILE_PATH = r"C:\Users\laurip\Documents\Outlook-tiedostot\KaikkiSähköpostit_Täydellinen_Vienti.pst"
    OUTPUT_DIR = "output"
    LOGS_DIR = "logs"
    
    # Date Filtering (past 2 years)
    START_DATE = datetime.now() - timedelta(days=2*365)  # 2 years ago
    END_DATE = datetime.now()
    
    # Email Filtering
    OFFER_KEYWORDS = ["tarjouspyyntö"]
    
    # Excel/Spreadsheet Processing
    MAX_EXCEL_ROWS = 1000
    SUPPORTED_EXCEL_FORMATS = ['.xlsx', '.xls', '.csv', '.ods']
    
    # AI Processing
    GEMINI_MODEL = "gemini-2.5-flash"  # Back to 2.5 Pro with fixed parsing
    GEMINI_MODEL_ITERATION = "gemini-2.5-flash"
    GEMINI_MODEL_THINKING = "gemini-2.5-pro"
    MAX_RETRIES = 3
    API_RETRY_DELAY = 1  # seconds
    
    # Semantic Search / Embedding Configuration
    MAX_EMBEDDING_PRODUCTS = int(os.getenv('MAX_EMBEDDING_PRODUCTS', '0'))     # 0 = process all products
    EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '1000'))     # OpenAI can handle up to 2048 inputs
    SEMANTIC_SIMILARITY_THRESHOLD = float(os.getenv('SEMANTIC_THRESHOLD', '0.15'))  # Minimum similarity
    
    # OpenAI Embedding Settings
    OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-large')  # Most cost-effective
    OPENAI_RATE_LIMIT_PER_MINUTE = int(os.getenv('OPENAI_RATE_LIMIT_PER_MINUTE', '100'))
    OPENAI_RATE_LIMIT_PER_DAY = int(os.getenv('OPENAI_RATE_LIMIT_PER_DAY', '2000'))
    OPENAI_TPM_LIMIT = int(os.getenv('OPENAI_TPM_LIMIT', '150000'))  # Tokens Per Minute limit (free tier)
    
    # RAG Pipeline Mode (set to True for single mega-batch processing)
    RAG_SINGLE_BATCH_MODE = os.getenv('RAG_SINGLE_BATCH_MODE', 'False').lower() == 'true'
    
    # Context Management for Batch Agent
    MAX_CONTEXT_TOKENS = 7000  # Max tokens for Gemini conversation context
    
    # Output Configuration
    OUTPUT_CSV_NAME = f"unclear_hvac_terms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    CSV_COLUMNS = ['unclear_term', 'quantity', 'explanation', 'email_subject', 'email_date', 'source_type', 'source_file']
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Known HVAC Examples for AI Context
    HVAC_EXAMPLES = [
        "1 1/2\"- 1/2\" musta suppari",  # unclear sizing notation
        "dn 100 musta putki",           # fairly clear
        "Kannakkeet: 28mm 10kpl",       # clear
        "fisher vahvaa c kiskoa 12m"    # brand/product unclear
    ]

# Create necessary directories if they don't exist
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True) 