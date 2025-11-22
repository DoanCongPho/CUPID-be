echo "Building project..."

# Ensure pip is installed/updated for 3.12
python3.12 -m ensurepip
python3.12 -m pip install --upgrade pip

# Install dependencies
python3.12 -m pip install -r requirements.txt

# Collect static files
python3.12 manage.py collectstatic --noinput --clear

echo "Build End"