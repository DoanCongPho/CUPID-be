# Models Refactoring Guide

## Overview
The `users/models.py` file has been refactored for better organization and maintainability while keeping all models in a single file (Django best practice for small to medium projects).

## Refactoring Summary

### ✅ What Was Done
1. **Added comprehensive docstring** at the top explaining the file structure
2. **Organized into 6 clear sections** with visual separators
3. **Enhanced all model docstrings** with relationships and purpose
4. **Added field comments** for better understanding
5. **Improved Meta classes** with verbose names and ordering
6. **Added method docstrings** for ExpiringToken methods
7. **Used constants** for choices (e.g., STATUS_SUCCESSFUL) for better code maintainability

### 📁 File Structure

```python
users/models.py (515 lines, organized)
├── SECTION 1: AUTHENTICATION MODELS (140 lines)
│   ├── User - Custom authentication model
│   └── ExpiringToken - Token-based auth with expiration
│
├── SECTION 2: USER PROFILE MODELS (80 lines)
│   ├── UserProfile - Extended user information
│   └── UserModeSettings - App settings/preferences
│
├── SECTION 3: TASK MODELS (35 lines)
│   └── Task - User tasks and to-do items
│
├── SECTION 4: MATCHING MODELS (130 lines)
│   ├── Match - Matches between users
│   └── Quests - Quest activities for matches
│
├── SECTION 5: CHAT MODELS (75 lines)
│   ├── Chat - Chat conversations
│   └── Message - Individual messages
│
└── SECTION 6: PREFERENCE MODELS (55 lines)
    ├── Preference - Lookup table for interests
    └── UserPreference - User-to-preference mapping
```

## Key Improvements

### 1. **Clear Section Headers**
```python
# ==============================================================================
# SECTION 1: AUTHENTICATION MODELS
# ==============================================================================
```
Makes it easy to navigate the file and understand its structure at a glance.

###2. **Enhanced Docstrings**
Before:
```python
class User(AbstractUser):
    """
    Lưu trữ thông tin cốt lõi dùng cho việc xác thực (đăng nhập/đăng ký).
    Đây là bảng trung tâm của hệ thống.
    """
```

After:
```python
class User(AbstractUser):
    """
    Custom User model for authentication.

    Lưu trữ thông tin cốt lõi dùng cho việc xác thực (đăng nhập/đăng ký).
    Đây là bảng trung tâm của hệ thống.

    Fields:
        email: Primary authentication field (unique)
        phone_number: Alternative authentication field (unique, optional)
        provider: OAuth provider name (e.g., "google", "facebook", "email")
        provider_id: External provider ID (e.g., Auth0 sub)
    """
```

### 3. **Relationship Documentation**
```python
class UserProfile(models.Model):
    """
    Extended user profile information.

    Relationships:
        - OneToOne with User (auto-created via signal)
    """
```

### 4. **Better Meta Classes**
```python
class Meta:
    verbose_name = _("task")
    verbose_name_plural = _("tasks")
    ordering = ["-created_at"]
```

### 5. **Method Documentation**
```python
@classmethod
def generate_token_for_user(cls, user, days_valid: int = 365, name: str = ""):
    """
    Generate a new token for a user.

    Args:
        user: User instance
        days_valid: Number of days until token expires (default 365)
        name: Optional label for the token

    Returns:
        tuple: (plaintext_token, token_object)

    Note:
        Return plaintext token to client ONCE. Server only stores hash.
    """
```

## Why Single File Instead of Package?

### ✅ Advantages of Single File (Current Approach)
1. **Simpler imports** - No circular dependency issues
2. **Django compatibility** - Native support, no special configuration
3. **Easier navigation** - One place to find all models
4. **Better for small/medium projects** - Your project has 10 models
5. **No migration headaches** - Django handles it naturally
6. **Faster development** - Less boilerplate

### ❌ Disadvantages of Models Package
1. **Import complexity** - Need careful `__init__.py` management
2. **Circular dependencies** - ForeignKey relationships become tricky
3. **Migration issues** - Django may not detect models correctly
4. **More boilerplate** - Need `__init__.py` with imports
5. **Overkill for small projects** - Adds unnecessary complexity

### 📊 When to Split into Package?
Consider splitting when:
- **50+ models** in a single app
- **Clear bounded contexts** that rarely interact
- **Multiple team members** working on different model groups
- **You have time** to handle the migration and testing overhead

## Best Practices Applied

### 1. **Naming Conventions**
- ✅ Models use singular names (`User`, not `Users`)
- ✅ Exception: `Quests` (existing, would require migration to change)
- ✅ Related names are descriptive (`matches_as_user1`, not `matches1`)

### 2. **Field Organization**
Within each model, fields are grouped logically:
```python
class UserProfile(models.Model):
    # Relationship
    user = models.OneToOneField(...)

    # Personal Information
    full_name = models.CharField(...)
    date_of_birth = models.DateField(...)

    # Media
    profile_photo_url = models.URLField(...)

    # Gamification
    total_xp = models.IntegerField(...)

    # Timestamps
    created_at = models.DateTimeField(...)
    updated_at = models.DateTimeField(...)
```

### 3. **Constants for Choices**
```python
# ✅ Good - reusable and type-safe
STATUS_SUCCESSFUL = "successful"
STATUS_EXPIRED = "expired"
STATUS_CHOICES = [
    (STATUS_SUCCESSFUL, "Successful"),
    (STATUS_EXPIRED, "Expired"),
]

# ❌ Bad - magic strings scattered everywhere
status = models.CharField(choices=[("successful", "Successful")])
```

### 4. **Verbose Names**
```python
class Meta:
    verbose_name = _("user profile")  # Translatable
    verbose_name_plural = _("user profiles")  # Correct plural
```

### 5. **Indexes for Performance**
```python
class Meta:
    indexes = [
        models.Index(fields=["external_id"]),  # Frequently queried
        models.Index(fields=["created_at"]),   # Used in ordering
    ]
```

## Navigation Tips

### Quick Jump to Sections
Search for these patterns in your editor:
- `SECTION 1` - Authentication models
- `SECTION 2` - Profile models
- `SECTION 3` - Task models
- `SECTION 4` - Matching models
- `SECTION 5` - Chat models
- `SECTION 6` - Preference models

### Find Specific Model
- Press `Cmd/Ctrl + F` and search: `class ModelName(`
- Example: `class Match(` will jump directly to Match model

### See All Relationships
Search for:
- `ForeignKey` - One-to-many relationships
- `OneToOneField` - One-to-one relationships
- `related_name` - Reverse relationship names

## Testing

All 55 tests pass after refactoring:
```bash
poetry run python manage.py test users --verbosity=1
# Result: Ran 55 tests in 10.814s - OK ✅
```

## Future Improvements

### When to Consider Further Refactoring:
1. **If models exceed 1000 lines** - Consider splitting
2. **If you add bounded contexts** - E.g., separate `payments` app
3. **If circular imports occur** - May need restructuring
4. **If team grows significantly** - Package structure helps parallel work

### Recommended Next Steps:
1. ✅ **Add model managers** for complex queries
   ```python
   class MatchManager(models.Manager):
       def active(self):
           return self.filter(status=Match.STATUS_SUCCESSFUL)
   ```

2. ✅ **Add model methods** for business logic
   ```python
   def is_expired(self):
       return self.status == self.STATUS_EXPIRED
   ```

3. ✅ **Add property decorators** for computed fields
   ```python
   @property
   def full_address(self):
       return f"{self.home_latitude},{self.home_longitude}"
   ```

4. ✅ **Add validation** in clean() methods
   ```python
   def clean(self):
       if self.user1 == self.user2:
           raise ValidationError("Cannot match with yourself")
   ```

## Conclusion

This refactoring improves code maintainability while keeping Django best practices. The single-file approach is perfect for your project size and complexity level.

**Before**: Unorganized 288-line file with minimal documentation
**After**: Well-organized 515-line file with comprehensive documentation and clear structure

All functionality preserved, all tests passing! 🎉
