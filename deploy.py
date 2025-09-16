#!/usr/bin/env python3
"""
Deployment helper script for InChrist AI
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if required tools are installed"""
    tools = {
        'git': 'Git is required for deployment',
        'docker': 'Docker is required for containerized deployment (optional)'
    }
    
    missing = []
    for tool, description in tools.items():
        if not shutil.which(tool):
            if tool == 'docker':
                print(f"⚠️  {description}")
            else:
                missing.append(f"❌ {description}")
    
    if missing:
        print("Missing required tools:")
        for msg in missing:
            print(msg)
        return False
    
    print("✅ All required tools are available")
    return True

def setup_environment():
    """Setup environment for deployment"""
    print("\n🔧 Setting up deployment environment...")
    
    # Check if config.py exists and has API keys
    if os.path.exists('config.py'):
        print("📋 Backing up your current config.py...")
        shutil.copy('config.py', 'config_backup.py')
        print("✅ Config backed up to config_backup.py")
    
    # Check if env.example exists
    if os.path.exists('env.example'):
        if not os.path.exists('.env'):
            print("📝 Creating .env template from env.example...")
            shutil.copy('env.example', '.env')
            print("⚠️  Please edit .env with your actual API keys!")
        else:
            print("ℹ️  .env file already exists")
    
    print("✅ Environment setup complete")

def git_setup():
    """Setup git repository if needed"""
    print("\n📦 Checking Git repository...")
    
    if not os.path.exists('.git'):
        print("Initializing Git repository...")
        subprocess.run(['git', 'init'], check=True)
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit for deployment'], check=True)
        print("✅ Git repository initialized")
    else:
        print("✅ Git repository already exists")
    
    # Check if there are uncommitted changes
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if result.stdout.strip():
        print("📝 Committing current changes...")
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Prepare for cloud deployment'], check=True)
        print("✅ Changes committed")

def show_deployment_options():
    """Show available deployment options"""
    print("\n🚀 Deployment Options:")
    print("=" * 50)
    
    options = [
        {
            'name': 'Railway.app',
            'difficulty': '🟢 Easiest',
            'cost': 'Free tier available',
            'features': '• Automatic deployments\n• Built-in PostgreSQL\n• Simple dashboard'
        },
        {
            'name': 'Heroku',
            'difficulty': '🟡 Medium',
            'cost': '$5-10/month',
            'features': '• Reliable platform\n• Great documentation\n• Add-ons ecosystem'
        },
        {
            'name': 'DigitalOcean',
            'difficulty': '🟡 Medium',
            'cost': '$5/month',
            'features': '• Good performance\n• Built-in monitoring\n• Competitive pricing'
        },
        {
            'name': 'Google Cloud Run',
            'difficulty': '🔴 Advanced',
            'cost': 'Pay per use',
            'features': '• Serverless scaling\n• Very cost effective\n• Enterprise grade'
        }
    ]
    
    for i, option in enumerate(options, 1):
        print(f"\n{i}. {option['name']} - {option['difficulty']}")
        print(f"   Cost: {option['cost']}")
        print(f"   Features:")
        for line in option['features'].split('\n'):
            print(f"   {line}")

def main():
    """Main deployment helper"""
    print("🌟 InChrist AI - Cloud Deployment Helper")
    print("=" * 40)
    
    # Check current directory
    if not os.path.exists('main.py'):
        print("❌ Please run this script from the InChristAI directory")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Git setup
    git_setup()
    
    # Show options
    show_deployment_options()
    
    print("\n📖 Next Steps:")
    print("1. Read DEPLOYMENT.md for detailed instructions")
    print("2. Edit .env with your API keys (NEVER commit this file!)")
    print("3. Choose a deployment platform and follow the guide")
    print("4. Test your deployment with the health check endpoints")
    
    print("\n🔗 Quick Links:")
    print("• Railway.app: https://railway.app")
    print("• Heroku: https://heroku.com")
    print("• DigitalOcean: https://www.digitalocean.com/products/app-platform")
    print("• Google Cloud: https://cloud.google.com/run")
    
    print("\n✨ Your bot is ready for cloud deployment!")

if __name__ == "__main__":
    main()
