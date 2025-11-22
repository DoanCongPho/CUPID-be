# build_files.sh
echo "Building..."

# Ensure pip is updated
python3.9 -m ensurepip
python3.9 -m pip install --upgrade pip

# Install the fixed requirements
python3.9 -m pip install -r requirements.txt

# Collect static files
python3.9 manage.py collectstatic --noinput --clear

echo "Build End"