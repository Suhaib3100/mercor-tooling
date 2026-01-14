#!/bin/bash
# Azure VM Setup Script for Mercor Pipeline
# Run this on your Azure VM after SSH'ing in

set -e

echo "🚀 Setting up Mercor Pipeline on Azure VM..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python..."
sudo apt install -y python3 python3-pip python3-venv git nginx

# Clone the repo (replace with your repo URL)
echo "📥 Cloning repository..."
cd ~
git clone https://github.com/Suhaib3100/mercor-tooling.git
cd mercor-tooling

# Create virtual environment
echo "🔧 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
echo "⚙️ Creating .env file..."
cat > .env << 'EOF'
AIRTABLE_API_KEY=your-airtable-token-here
AIRTABLE_BASE_ID=appjkWw6Z1fgtGTgi
LLM_API_KEY=your-openai-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
EOF

echo "⚠️  IMPORTANT: Edit .env with your actual API keys!"
echo "   nano ~/mercor-tooling/.env"

# Setup systemd service
echo "🔄 Setting up systemd service..."
sudo cp mercor-pipeline.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mercor-pipeline
sudo systemctl start mercor-pipeline

# Setup Nginx
echo "🌐 Setting up Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/mercor-pipeline
sudo ln -sf /etc/nginx/sites-available/mercor-pipeline /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Open firewall ports
echo "🔥 Configuring firewall..."
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw --force enable

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit your .env file with real API keys:"
echo "   nano ~/mercor-tooling/.env"
echo ""
echo "2. Restart the service after editing .env:"
echo "   sudo systemctl restart mercor-pipeline"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status mercor-pipeline"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u mercor-pipeline -f"
echo ""
echo "5. Your webhook URL is:"
echo "   http://YOUR-VM-IP/webhook/new-application"
echo ""
echo "6. Test with:"
echo "   curl http://localhost/health"
