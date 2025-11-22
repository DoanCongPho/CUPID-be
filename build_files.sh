# build_files.sh

echo "Building project..."

# Ensure pip is installed for Python 3.11
python3.11 -m ensurepip
python3.11 -m pip install --upgrade pip

# Install dependencies using Python 3.11
python3.11 -m pip install -r requirements.txt

# Collect static files
python3.11 manage.py collectstatic --noinput --clear

echo "Build End"