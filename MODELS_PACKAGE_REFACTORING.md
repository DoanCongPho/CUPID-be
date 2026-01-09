# Models Package Refactoring - Complete Guide

## ✅ Successfully Refactored!

Your `users/models.py` file has been refactored into a **models package structure** with separate files for each domain.

## 📁 New Structure

```
users/
├── models/                          # Models package directory
│   ├── __init__.py                  # Package initializer (imports all models)
│   ├── user.py                      # User authentication model
│   ├── token.py                     # ExpiringToken model
│   ├── profile.py                   # UserProfile & UserModeSettings
│   ├── task.py                      # Task model
│   ├── match.py                     # Match & Quests models
│   ├── chat.py                      # Chat & Message models
│   └── preference.py                # Preference & UserPreference models
│
├── models_single_file.py.backup     # Original single-file backup
└── models.py.backup                 # Another backup
```

## 📄 File Breakdown

### 1. **`models/user.py`** (29 lines)
- `User` - Custom authentication model
- Fields: email, phone_number, provider, provider_id
- Extends Django's AbstractUser

### 2. **`models/token.py`** (76 lines)
- `ExpiringToken` - Token-based authentication
- Methods:
  - `_hash_token()` - SHA256 hashing
  - `generate_token_for_user()` - Create new tokens
  - `verify_token()` - Validate tokens
  - `revoke()` - Revoke tokens

### 3. **`models/profile.py`** (64 lines)
- `UserProfile` - Extended user information
  - Personal info, media, gamification, location
- `UserModeSettings` - App preferences
  - Ghost mode, reminders, location sharing, notifications

### 4. **`models/task.py`** (30 lines)
- `Task` - User tasks and to-do items
- Fields: description, scheduled times, is_free

### 5. **`models/match.py`** (104 lines)
- `Match` - Matches between users
  - Status choices: successful, user1_missed, user2_missed, expired
  - Ratings for both users
- `Quests` - Quest activities for matches
  - Location, activity, quest_date, status, xp_reward

### 6. **`models/chat.py`** (68 lines)
- `Chat` - Chat conversations
  - OneToOne with Match (uses string reference to avoid circular import)
  - Status: active, closed
- `Message` - Individual messages
  - ForeignKey to Chat and User (sender)

### 7. **`models/preference.py`** (49 lines)
- `Preference` - Lookup table for interests
- `UserPreference` - Many-to-many relationship

### 8. **`models/__init__.py`** (37 lines)
- **Most Important File!**
- Imports all models in correct order
- Exports them for backward compatibility

## 🔑 Key Features

### 1. **Import Order Matters**
```python
# In __init__.py
from .user import User                              # 1. User first (AUTH_USER_MODEL)
from .token import ExpiringToken                    # 2. Independent models
from .profile import UserProfile, UserModeSettings
from .task import Task
from .match import Match, Quests                    # 3. Models with User FK
from .chat import Chat, Message                     # 4. Models with Match FK
from .preference import Preference, UserPreference
```

### 2. **Avoiding Circular Imports**
In `chat.py`, Match is referenced as a string:
```python
match = models.OneToOneField(
    "Match",  # String reference, not direct import!
    on_delete=models.CASCADE,
    related_name="chat",
)
```

### 3. **Backward Compatibility**
All existing imports still work:
```python
from users.models import User, Match, Task  # ✅ Works perfectly
```

## ✅ Test Results

```bash
poetry run python manage.py test users --verbosity=1
# Found 55 test(s).
# Ran 55 tests in 10.382s
# OK ✅
```

## 📊 Benefits of This Structure

### ✅ Advantages
1. **Better Organization** - Each domain in its own file
2. **Easier Navigation** - Find models quickly
3. **Clearer Responsibilities** - Each file has a single purpose
4. **Maintainability** - Easier to modify individual models
5. **Team Collaboration** - Reduced merge conflicts
6. **Scalability** - Easy to add new model files

### 📈 File Size Comparison

| Before | After |
|--------|-------|
| 1 file (515 lines) | 8 files (30-104 lines each) |
| Hard to navigate | Easy to find specific models |
| Single responsibility violated | Single responsibility per file |

## 🔍 How to Use

### Import All Models
```python
from users.models import (
    User, ExpiringToken,
    UserProfile, UserModeSettings,
    Task, Match, Quests,
    Chat, Message,
    Preference, UserPreference
)
```

### Import Specific Model
```python
from users.models import User
from users.models import Match, Quests
from users.models.chat import Chat, Message  # Direct import from file
```

### In Django Admin
```python
from users.models import User, Task, Match
# Works exactly as before!
```

## 🛠️ Adding New Models

### Step 1: Create New File
```bash
cd users/models
touch billing.py
```

### Step 2: Define Model
```python
# users/models/billing.py
from django.db import models
from django.conf import settings

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Step 3: Update __init__.py
```python
# users/models/__init__.py
from .user import User
# ...existing imports...
from .billing import Payment  # Add new import

__all__ = [
    'User',
    # ...existing exports...
    'Payment',  # Add to exports
]
```

### Step 4: Make Migrations
```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

## 🔧 Troubleshooting

### Issue 1: Import Errors
**Problem:** `ImportError: cannot import name 'User'`

**Solution:**
1. Check `__init__.py` imports all models
2. Clear Python caches: `find . -name "*.pyc" -delete`
3. Restart Django development server

### Issue 2: Circular Import
**Problem:** `ImportError: cannot import name 'Match' from partially initialized module`

**Solution:**
- Use string references for ForeignKey/OneToOneField:
```python
# ❌ Bad
from .match import Match
match = models.ForeignKey(Match, ...)

# ✅ Good
match = models.ForeignKey("Match", ...)
```

### Issue 3: Model Not Found
**Problem:** `LookupError: App 'users' doesn't have a 'User' model`

**Solution:**
1. Ensure model is imported in `__init__.py`
2. Clear `__pycache__` directories
3. Check file names match imports

## 📚 Best Practices

### 1. **One Domain Per File**
- ✅ `match.py` contains Match and Quests (same domain)
- ✅ `chat.py` contains Chat and Message (same domain)
- ❌ Don't mix unrelated models in one file

### 2. **Import Order in __init__.py**
```python
# 1. Core models (User)
# 2. Independent models (no FK to other app models)
# 3. Dependent models (FK to User)
# 4. Highly dependent models (FK to other app models)
```

### 3. **String References for Cross-File FKs**
```python
# When referencing models from other files in same app
models.ForeignKey("ModelName", ...)  # String reference
```

### 4. **Keep __init__.py Updated**
Always add new models to:
- Import statements
- `__all__` list

## 🎯 Quick Reference

| Task | Command/Location |
|------|------------------|
| Find User model | `users/models/user.py` |
| Find Match logic | `users/models/match.py` |
| Add new model | Create file → Edit `__init__.py` |
| Import all models | `from users.models import *` |
| Run tests | `poetry run python manage.py test users` |
| Make migrations | `poetry run python manage.py makemigrations` |

## 📝 Migration Notes

- **No data migration needed** - Same database structure
- **No code changes needed** in views/serializers
- All existing imports work without modification
- Signals still work (`users.signals` references `users.models`)

## 🔄 Rollback Instructions

If you need to revert to single file:

```bash
cd users
rm -rf models/
cp models_single_file.py.backup models.py
find . -name "__pycache__" -type d -exec rm -rf {} +
poetry run python manage.py test users
```

## ✨ Summary

✅ **Refactoring Complete!**
- 8 organized model files
- 55/55 tests passing
- Zero breaking changes
- Better maintainability
- Ready for scaling

**Before:** 1 monolithic file
**After:** Clean package structure with single responsibilities

🎉 Your models are now much better organized!
