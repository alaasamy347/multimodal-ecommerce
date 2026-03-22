#!/bin/bash

echo "=================================================="
echo "🎤 Voice Search Setup"
echo "=================================================="

# Check if OpenAI package is installed
echo ""
echo "1️⃣ Installing OpenAI package..."
pip install openai

if [ $? -eq 0 ]; then
    echo "✅ OpenAI package installed"
else
    echo "❌ Failed to install OpenAI package"
    exit 1
fi

# Check for API key
echo ""
echo "2️⃣ Checking for OpenAI API key..."

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not found in environment"
    echo ""
    echo "📋 To set up:"
    echo "   1. Get API key from: https://platform.openai.com/api-keys"
    echo "   2. Set environment variable:"
    echo ""
    echo "      # For current session (temporary):"
    echo "      export OPENAI_API_KEY='sk-proj-...'"
    echo ""
    echo "      # For permanent (Linux/Mac):"
    echo "      echo 'export OPENAI_API_KEY=\"sk-proj-...\"' >> ~/.bashrc"
    echo "      source ~/.bashrc"
    echo ""
    echo "      # For permanent (Windows PowerShell):"
    echo "      [System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-...', 'User')"
    echo ""
    echo "   3. Restart terminal and run this script again"
    exit 1
else
    echo "✅ OPENAI_API_KEY found"
    echo "   Key starts with: ${OPENAI_API_KEY:0:10}..."
fi

# Test the setup
echo ""
echo "3️⃣ Testing voice search..."
echo ""

# Create a test audio file (you'll need to record actual audio)
echo "   To test voice search:"
echo "   1. Start backend: python main.py"
echo "   2. Go to frontend and click microphone button"
echo "   3. Say something like 'brown bed'"
echo "   4. Check backend logs for:"
echo "      🎤 Transcribing audio file: ..."
echo "      ✅ Transcription: 'brown bed'"

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "📋 Next steps:"
echo "   1. Make sure OPENAI_API_KEY is set"
echo "   2. Restart backend: python main.py"
echo "   3. Test voice search in the frontend"
echo ""
echo "💰 Cost: ~$0.006 per minute of audio"
echo "   (Very cheap for occasional use)"
echo ""
echo "=================================================="