# Preferences API Documentation

## Overview

The Preferences API allows users to manage preference categories and associate them with their profiles. This is used for matching users based on shared interests, hobbies, or characteristics.

---

## Table of Contents

1. [Models](#models)
2. [Serializers](#serializers)
3. [Views & Endpoints](#views--endpoints)
4. [Test Coverage](#test-coverage)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)

---

## Models

### 1. `Preference` Model
**Location**: `users/models/preference.py`

Represents a preference category (e.g., "Sports", "Music", "Travel").

```python
class Preference(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

**Fields**:
- `name` (CharField, max 100, unique) - The preference name
- `description` (TextField, optional) - Description of the preference
- `created_at` (DateTime) - Timestamp when preference was created

---

### 2. `UserPreference` Model
**Location**: `users/models/preference.py`

Links users to their selected preferences (many-to-many relationship).

```python
class UserPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_preferences')
    preference = models.ForeignKey(Preference, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'preference')

    def __str__(self):
        return f"{self.user.email} - {self.preference.name}"
```

**Fields**:
- `user` (ForeignKey) - Reference to User model
- `preference` (ForeignKey) - Reference to Preference model
- `created_at` (DateTime) - When user added this preference

**Constraints**:
- `unique_together` on (`user`, `preference`) - Prevents duplicate preferences per user

---

## Serializers

### 1. `PreferenceSerializer`
**Location**: `users/serializers/preference.py`

Serializes preference objects for API responses.

```python
class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']
```

**Fields**:
- `id` (read-only) - Preference ID
- `name` (required) - Preference name
- `description` (optional) - Preference description
- `created_at` (read-only) - Creation timestamp

---

### 2. `UserPreferenceSerializer`
**Location**: `users/serializers/preference.py`

Serializes user-preference associations with nested preference data.

```python
class UserPreferenceSerializer(serializers.ModelSerializer):
    preference = PreferenceSerializer(read_only=True)
    preference_id = serializers.PrimaryKeyRelatedField(
        queryset=Preference.objects.all(),
        write_only=True,
        source='preference'
    )

    class Meta:
        model = UserPreference
        fields = ['id', 'preference', 'preference_id', 'created_at']
        read_only_fields = ['id', 'created_at']
```

**Fields**:
- `id` (read-only) - UserPreference ID
- `preference` (read-only, nested) - Full preference object in responses
- `preference_id` (write-only) - Preference ID for creating associations
- `created_at` (read-only) - When preference was added to user

---

## Views & Endpoints

### 1. `PreferenceListCreateView`
**Location**: `users/views/preference.py`

List all available preferences or create new ones.

**Endpoint**: `GET/POST /api/preferences/`

**Permissions**: `AllowAny` (public access)

**Methods**:
- `GET` - List all preferences (ordered by name)
- `POST` - Create a new preference (admin use)

**Response Format** (GET):
```json
[
    {
        "id": 1,
        "name": "Sports",
        "description": "Interest in sports activities",
        "created_at": "2025-12-15T10:00:00Z"
    },
    {
        "id": 2,
        "name": "Music",
        "description": "Interest in music",
        "created_at": "2025-12-15T10:05:00Z"
    }
]
```

**Request Format** (POST):
```json
{
    "name": "Travel",
    "description": "Interest in traveling"
}
```

---

### 2. `UserPreferenceListCreateView`
**Location**: `users/views/preference.py`

List user's preferences or add new preferences to their profile.

**Endpoint**: `GET/POST /api/user-preferences/`

**Permissions**: `IsAuthenticated`

**Methods**:
- `GET` - List authenticated user's preferences
- `POST` - Add a preference to authenticated user's profile

**Response Format** (GET):
```json
[
    {
        "id": 10,
        "preference": {
            "id": 1,
            "name": "Sports",
            "description": "Interest in sports activities",
            "created_at": "2025-12-15T10:00:00Z"
        },
        "created_at": "2025-12-15T12:30:00Z"
    },
    {
        "id": 11,
        "preference": {
            "id": 3,
            "name": "Travel",
            "description": "Interest in traveling",
            "created_at": "2025-12-15T10:10:00Z"
        },
        "created_at": "2025-12-15T12:35:00Z"
    }
]
```

**Request Format** (POST):
```json
{
    "preference_id": 2
}
```

**Response** (POST 201 Created):
```json
{
    "id": 12,
    "preference": {
        "id": 2,
        "name": "Music",
        "description": "Interest in music",
        "created_at": "2025-12-15T10:05:00Z"
    },
    "created_at": "2025-12-15T13:00:00Z"
}
```

**Features**:
- Uses `get_or_create()` to prevent duplicate preferences
- Returns existing preference if already added
- Automatically associates with authenticated user

---

### 3. `UserPreferenceDestroyView`
**Location**: `users/views/preference.py`

Remove a preference from user's profile.

**Endpoint**: `DELETE /api/user-preferences/<pref_id>/`

**Permissions**: `IsAuthenticated`

**URL Parameters**:
- `pref_id` - The preference ID to remove

**Response** (204 No Content):
```
(empty response body)
```

**Error Response** (404 Not Found):
```json
{
    "detail": "Not found."
}
```

**Features**:
- Only allows users to delete their own preferences
- Returns 404 if preference doesn't exist or doesn't belong to user

---

## Test Coverage

### ✅ All 6 Preference Tests Passing

**Test File**: `users/tests/test_services.py` → `PreferenceAPITests`

#### Test Cases:

1. **`test_list_preferences`** ✅
   - Verifies all preferences are listed
   - Checks ordering by name
   - Public access (no authentication required)

2. **`test_create_preference`** ✅
   - Creates new preference category
   - Validates required fields
   - Returns created preference data

3. **`test_add_user_preference`** ✅
   - Adds preference to authenticated user
   - Verifies preference association
   - Returns nested preference data

4. **`test_list_user_preferences`** ✅
   - Lists all user's preferences
   - Checks nested preference objects
   - Verifies ordering by created_at

5. **`test_delete_user_preference`** ✅
   - Removes preference from user
   - Verifies 204 No Content response
   - Confirms preference is deleted

6. **`test_cannot_add_duplicate_preference`** ✅
   - Prevents duplicate preferences per user
   - Validates unique_together constraint
   - Returns appropriate error response

---

## Usage Examples

### Example 1: List All Available Preferences

**Request**:
```bash
curl -X GET http://localhost:8000/api/preferences/
```

**Response**:
```json
[
    {"id": 1, "name": "Sports", "description": "...", "created_at": "..."},
    {"id": 2, "name": "Music", "description": "...", "created_at": "..."},
    {"id": 3, "name": "Travel", "description": "...", "created_at": "..."}
]
```

---

### Example 2: Add Preference to User Profile

**Request**:
```bash
curl -X POST http://localhost:8000/api/user-preferences/ \
  -H "Authorization: Token your-auth-token" \
  -H "Content-Type: application/json" \
  -d '{"preference_id": 1}'
```

**Response**:
```json
{
    "id": 10,
    "preference": {
        "id": 1,
        "name": "Sports",
        "description": "Interest in sports activities",
        "created_at": "2025-12-15T10:00:00Z"
    },
    "created_at": "2025-12-15T13:00:00Z"
}
```

---

### Example 3: Get User's Preferences

**Request**:
```bash
curl -X GET http://localhost:8000/api/user-preferences/ \
  -H "Authorization: Token your-auth-token"
```

**Response**:
```json
[
    {
        "id": 10,
        "preference": {
            "id": 1,
            "name": "Sports",
            "description": "Interest in sports activities",
            "created_at": "2025-12-15T10:00:00Z"
        },
        "created_at": "2025-12-15T13:00:00Z"
    },
    {
        "id": 11,
        "preference": {
            "id": 3,
            "name": "Travel",
            "description": "Interest in traveling",
            "created_at": "2025-12-15T10:10:00Z"
        },
        "created_at": "2025-12-15T13:05:00Z"
    }
]
```

---

### Example 4: Remove Preference from User Profile

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/user-preferences/1/ \
  -H "Authorization: Token your-auth-token"
```

**Response**:
```
204 No Content
```

---

### Example 5: Register User with Preferences

**Request**:
```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1995-05-15",
    "preferences": [1, 2, 3]
  }'
```

**Response**:
```json
{
    "user": {
        "id": 5,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "profile": {
        "id": 5,
        "date_of_birth": "1995-05-15",
        "preferences": [
            {"id": 1, "name": "Sports", "...": "..."},
            {"id": 2, "name": "Music", "...": "..."},
            {"id": 3, "name": "Travel", "...": "..."}
        ]
    },
    "token": "abc123..."
}
```

---

## Best Practices

### ✅ For Frontend Developers

1. **Cache Preferences List**
   - Preferences are relatively static
   - Fetch once on app load and cache locally
   - Refresh periodically (daily/weekly)

2. **Show Preferences During Registration**
   - Display all available preferences as checkboxes/chips
   - Allow users to select multiple preferences
   - Include preferences in registration payload

3. **Real-time Preference Management**
   - Allow users to add/remove preferences from their profile
   - Update UI immediately after successful API calls
   - Show loading states during operations

4. **Error Handling**
   ```javascript
   // Handle duplicate preference
   if (response.status === 400 && response.data.includes('duplicate')) {
       showMessage('You already have this preference');
   }
   ```

---

### ✅ For Backend Developers

1. **Use `get_or_create()` Pattern**
   ```python
   # Prevents duplicates and simplifies code
   UserPreference.objects.get_or_create(
       user=request.user,
       preference=preference
   )
   ```

2. **Optimize Queries**
   ```python
   # Use select_related to avoid N+1 queries
   UserPreference.objects.filter(user=user).select_related('preference')
   ```

3. **Validate Preference Existence**
   - Use `get_object_or_404()` for preference lookups
   - Return appropriate error messages

4. **Consider Soft Deletes**
   - For analytics, consider tracking when preferences were removed
   - Use a `deleted_at` field instead of hard deletes

---

### ✅ Data Integrity

1. **Unique Constraints**
   ```python
   class Meta:
       unique_together = ('user', 'preference')
   ```
   - Enforced at database level
   - Prevents duplicate preferences per user

2. **Cascade Deletion**
   - User deleted → UserPreferences deleted automatically
   - Preference deleted → Consider impact on existing users

3. **Validation**
   - Ensure preference_id exists before creating association
   - Use serializer validation for complex rules

---

## URL Configuration

**File**: `users/urls.py`

```python
from django.urls import path
from .views import (
    PreferenceListCreateView,
    UserPreferenceListCreateView,
    UserPreferenceDestroyView,
)

urlpatterns = [
    # Preferences
    path('preferences/', PreferenceListCreateView.as_view(), name='preference-list-create'),
    path('user-preferences/', UserPreferenceListCreateView.as_view(), name='user-preference-list-create'),
    path('user-preferences/<int:pref_id>/', UserPreferenceDestroyView.as_view(), name='user-preference-destroy'),
]
```

---

## OpenAPI/Swagger Documentation

The views are decorated with `@extend_schema_view` for automatic API documentation:

**Access Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`

Features:
- Interactive API testing
- Request/response examples
- Authentication testing
- Model schemas

---

## Common Issues & Solutions

### Issue 1: Duplicate Preference Error
**Problem**: User tries to add preference they already have

**Solution**: The view uses `get_or_create()` which handles this automatically. Returns existing preference instead of error.

---

### Issue 2: Cannot Delete Non-Existent Preference
**Problem**: 404 error when trying to delete preference

**Cause**: Preference doesn't exist or doesn't belong to user

**Solution**:
```python
# View automatically checks ownership
get_object_or_404(UserPreference, user=request.user, preference_id=pref_id)
```

---

### Issue 3: Performance with Many Preferences
**Problem**: Slow queries when fetching user preferences

**Solution**: Use `select_related()` to optimize:
```python
UserPreference.objects.filter(user=user).select_related('preference')
```

---

## Migration Guide

### Adding New Preferences

```python
# In Django shell or migration
from users.models import Preference

# Create preferences
preferences = [
    Preference(name="Sports", description="Interest in sports activities"),
    Preference(name="Music", description="Interest in music"),
    Preference(name="Travel", description="Interest in traveling"),
    Preference(name="Reading", description="Interest in reading"),
    Preference(name="Cooking", description="Interest in cooking"),
]
Preference.objects.bulk_create(preferences, ignore_conflicts=True)
```

---

## Summary

✅ **3 API Endpoints**
- List/Create preferences (public)
- List/Add user preferences (authenticated)
- Remove user preferences (authenticated)

✅ **6 Comprehensive Tests**
- All CRUD operations covered
- Authorization and validation tested
- Duplicate prevention verified

✅ **Clean Architecture**
- Models, serializers, and views properly separated
- Follows Django REST Framework best practices
- Well-documented with OpenAPI schema

✅ **Production Ready**
- Optimized queries with `select_related()`
- Proper error handling
- Database constraints enforced
- Comprehensive test coverage

---

## Related Documentation

- [Models Package Refactoring](MODELS_PACKAGE_REFACTORING.md)
- [Serializers Package Refactoring](SERIALIZERS_PACKAGE_REFACTORING.md)
- [Views Package Refactoring](VIEWS_PACKAGE_REFACTORING.md)
- [Test Suite Summary](TEST_SUMMARY.md)
- [Authentication API Documentation](AUTHENTICATION_API_DOCUMENTATION.md) (if exists)
