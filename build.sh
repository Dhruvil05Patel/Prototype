#!/bin/bash

# Build script for deployment
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Frontend build completed!"
echo "Build files are in frontend/dist/"
