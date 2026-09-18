# Cupid Backend API

Backend API for the Cupid dating application built with Django REST Framework and Django Channels for real-time chat functionality.

## Prerequisites

- **Python 3.8+** installed
- **Poetry** for dependency and virtual environment management
- **(Optional)** Docker for running Redis or PostgreSQL locally

### Install Poetry

```bash
# Via official installer (recommended)
curl -sSL https://install.python-poetry.org | python3 -

# Or via pipx
pipx install poetry
```

Verify installation:
```bash
poetry --version
```

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

**Important:** Edit `.env` and ensure:
- No extra spaces around `=` (use `DEBUG=True` not `DEBUG= True`)
- No extra quotes around values
- Set `DEBUG=True` for local development
- Set `ALLOWED_HOSTS=localhost,127.0.0.1` for local development

Minimal `.env` for local development:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Database Setup

Apply migrations:
```bash
poetry run python manage.py migrate
```

Create a superuser (optional, for admin access):
```bash
poetry run python manage.py createsuperuser
```

## Running the Server

### Option 1: Django Development Server (API Only)

For basic API development without WebSocket support:
```bash
poetry run python manage.py runserver
```

### Option 2: ASGI Server (Recommended for Chat)

For full WebSocket/real-time chat support:

**Using Uvicorn (recommended):**
```bash
poetry run uvicorn config.asgi:application --host 127.0.0.1 --port 8000 --reload --log-level debug
```

**Using Daphne:**
```bash
poetry run daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

Server will be available at: `http://127.0.0.1:8000`

## API Documentation

Access interactive API documentation while the server is running:

- **OpenAPI Schema:** http://127.0.0.1:8000/api/schema/
- **Swagger UI:** http://127.0.0.1:8000/api/docs/swagger/
- **ReDoc:** http://127.0.0.1:8000/api/docs/redoc/
- **WebSocket Test UI:** http://127.0.0.1:8000/api/chat_ws_test.html

## Configuration

### Database Options

- **Local Development (default):** SQLite - no configuration needed
- **Production/Custom Database:** Set `DATABASE_URL` in `.env`
  ```env
  DATABASE_URL=postgresql://user:password@localhost:5432/dbname
  ```

### Channel Layers (WebSocket)

- **Local Development:** In-memory channel layer (no Redis required)
- **Production:** Configure Redis in `settings.py` and set:
  ```env
  REDIS_URL=redis://127.0.0.1:6379/0
  ```

### Authentication (Optional)

For Auth0 integration:
```env
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=your-api-identifier
```

For Supabase integration:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

## Development Tips

### Using Poetry Commands

Execute commands without activating the virtual environment:
```bash
poetry run <command>
```

Or activate the Poetry shell:
```bash
poetry shell
python manage.py runserver  # Now runs in activated environment
```

### Common Commands

```bash
# Create new Django app
poetry run python manage.py startapp app_name

# Make migrations after model changes
poetry run python manage.py makemigrations

# Apply migrations
poetry run python manage.py migrate

# Run tests
poetry run python manage.py test

# Collect static files (for deployment)
poetry run python manage.py collectstatic
```

### Database Migration Tips

If you encounter migration conflicts or issues:

```bash
# Reset local database (development only - destroys data!)
rm db.sqlite3
poetry run python manage.py migrate

# Fake migrations if tables already exist
poetry run python manage.py migrate --fake
```

**Note:** Ensure the `users/migrations/` chain is consistent before running migrations. If the database already contains tables, you may need `--fake` or to reset the development database.

### WebSocket Development

When testing Channels/WebSocket functionality locally:
- Use Uvicorn or Daphne (not `runserver`)
- For production, configure Redis; for development, the in-memory channel layer works fine

## Developer Notes

1. **Registration Flow:** User registration supports attaching preferences. Review `users/serializers/auth.py` and `users/views/auth.py` when modifying registration fields.

2. **API Schema:** Use the drf-spectacular endpoints (`/api/docs/swagger/`) to validate serializers and view schema annotations after making model or serializer changes.

3. **Testing:** The test suite automatically uses SQLite for faster execution regardless of your production database configuration.

4. **Environment Variables:** Ensure `.env` values don't include extra quotes or spaces. For example, use `REDIS_URL=redis://127.0.0.1:6379/0` not `REDIS_URL="redis://127.0.0.1:6379/0"`.

## Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. **Fork the repository** and clone your fork locally
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. **Set up your environment** following the Quick Start guide above
2. **Make your changes** with clear, descriptive commits
3. **Write tests** for new functionality
4. **Run the test suite** to ensure everything passes:
   ```bash
   poetry run python manage.py test
   ```
5. **Update documentation** if you're adding new features or changing APIs
6. **Validate API schema** using Swagger UI to ensure endpoints are properly documented

### Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and modular

### Submitting Changes

1. **Commit your changes** with descriptive messages:
   ```bash
   git commit -m "Add feature: brief description of changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request** with:
   - Clear title describing the change
   - Description of what was changed and why
   - Any related issue numbers
   - Screenshots/examples if applicable

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally (`poetry run python manage.py test`)
- [ ] New features include appropriate tests
- [ ] Documentation updated (README, docstrings, API docs)
- [ ] No unnecessary dependencies added
- [ ] Migrations are included if models changed
- [ ] Commit messages are clear and descriptive

### Reporting Issues

When reporting bugs or requesting features:
- Use the GitHub issue tracker
- Include steps to reproduce (for bugs)
- Provide error messages and logs
- Specify your environment (OS, Python version, etc.)

### Questions?

Feel free to open an issue for questions or join our development discussions.

## Troubleshooting

### "You must set settings.ALLOWED_HOSTS if DEBUG is False"

- Ensure `DEBUG=True` in `.env` with no spaces around `=`
- Set `ALLOWED_HOSTS=localhost,127.0.0.1` in `.env`
- Verify `.env` file is in project root (same directory as `manage.py`)

### WebSocket Connection Issues

- Use Uvicorn or Daphne instead of `runserver` for WebSocket support
- For production, ensure Redis is running and configured correctly

### Database Errors

- For local development, remove `DATABASE_URL` from `.env` to use SQLite
- Check database credentials and network connectivity for production databases
- Ensure migrations are up to date: `poetry run python manage.py migrate`

