#!/bin/bash

# AI Models Installation Script
# Downloads and initializes all required AI models for patent-worthy MCP server

set -e  # Exit on error

echo "================================================"
echo "🤖 AI Models Installation for Paramount+ MCP"
echo "================================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version || {
    echo "❌ Python 3 is required but not found"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip

# Install AI dependencies
echo "✓ Installing AI dependencies from requirements-ai.txt..."
pip install -r requirements-ai.txt

echo ""
echo "================================================"
echo "📦 Downloading AI Models"
echo "================================================"
echo ""

# 1. Download spaCy language model
echo "1️⃣  Downloading spaCy English language model (en_core_web_sm)..."
python -m spacy download en_core_web_sm

# 2. Download sentence-transformers model (cached automatically)
echo ""
echo "2️⃣  Downloading sentence-transformers model (all-MiniLM-L6-v2)..."
python -c "from sentence_transformers import SentenceTransformer; print('Loading model...'); model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('✓ Model cached successfully')"

# 3. Download CLIP model (for computer vision)
echo ""
echo "3️⃣  Downloading CLIP model (openai/clip-vit-base-patch32)..."
python -c "from transformers import CLIPModel, CLIPProcessor; print('Loading CLIP model...'); model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32'); print('✓ CLIP model cached successfully')"

# 4. Download Whisper model (for voice AI)
echo ""
echo "4️⃣  Downloading Whisper model (base)..."
python -c "import whisper; print('Loading Whisper model...'); model = whisper.load_model('base'); print('✓ Whisper model cached successfully')"

# 5. Initialize ChromaDB
echo ""
echo "5️⃣  Initializing ChromaDB vector database..."
python -c "import chromadb; client = chromadb.Client(); print('✓ ChromaDB initialized successfully')"

# 6. Download NLTK data
echo ""
echo "6️⃣  Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); print('✓ NLTK data downloaded')"

echo ""
echo "================================================"
echo "🎉 AI Models Installation Complete!"
echo "================================================"
echo ""
echo "Models downloaded:"
echo "  ✓ spaCy (en_core_web_sm) - NLP"
echo "  ✓ sentence-transformers (all-MiniLM-L6-v2) - Semantic search"
echo "  ✓ CLIP (openai/clip-vit-base-patch32) - Computer vision"
echo "  ✓ Whisper (base) - Speech-to-text"
echo "  ✓ ChromaDB - Vector database"
echo "  ✓ NLTK data - Natural language toolkit"
echo ""
echo "Total size: ~2.5GB"
echo ""
echo "You can now run the MCP server with:"
echo "  python -m mcp.server"
echo ""
