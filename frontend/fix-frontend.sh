#!/bin/bash

echo "🔧 Fixing Frontend Issues..."

# Navigate to frontend directory
cd frontend

# 1. Remove incompatible packages
echo "📦 Removing incompatible packages..."
npm uninstall react-router-dom @tailwindcss/postcss tailwindcss

# 2. Install correct Tailwind v3
echo "✅ Installing Tailwind CSS v3..."
npm install -D tailwindcss@3.4.17 postcss@latest autoprefixer@latest

# 3. Generate Tailwind config
echo "⚙️ Generating Tailwind config..."
npx tailwindcss init -p

# 4. Clean build cache
echo "🧹 Cleaning build cache..."
rm -rf .next
rm -rf node_modules/.cache

echo "✅ Frontend fixed! Now run: npm run dev"