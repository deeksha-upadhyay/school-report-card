#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Install wkhtmltopdf
apt-get update
apt-get install -y wkhtmltopdf
