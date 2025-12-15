# Test Suite Summary

## Test Files Created

The test suite has been split into two separate files for better organization:

### 1. `users/tests_auth.py` - Authentication Tests
Contains all authentication-related tests:
- **UserRegistrationTests** (10 tests)
  - Register with email only
  - Register with phone only
  - Register with preferences
  - Register with all fields
  - Validation tests (duplicate email/phone, underage, invalid date, etc.)

- **UserLoginTests** (7 tests)
  - Login with email
  - Login with phone
  - Wrong password
  - Non-existent user
  - Case-insensitive email
  - Returns full user info

- **LogoutTests** (2 tests)
  - Logout revokes token
  - Logout without authentication fails

- **TokenManagementTests** (2 tests)
  - List user tokens
  - List tokens without authentication fails

**Total: 21 authentication tests**

### 2. `users/tests_services.py` - Service/API Tests
Contains all business logic and service tests:
- **UserProfileTests** (3 tests)
  - Get profile
  - Update profile
  - Profile without authentication

- **TaskAPITests** (6 tests)
  - Create, list, get, update, delete tasks
  - Cannot access other user's tasks

- **UserModeSettingsAPITests** (2 tests)
  - Get/create settings
  - Update settings

- **MatchAPITests** (6 tests)
  - Create, list, get, update matches
  - Match with specific user endpoint
  - Cannot match with self

- **QuestAPITests** (4 tests)
  - Create, list, update, delete quests

- **ChatAndMessageAPITests** (7 tests)
  - Create, list chats
  - Send, list messages
  - Messages ordered by sent_at
  - Cannot send to other user's chat

- **PreferenceAPITests** (6 tests)
  - List, create preferences
  - Add, list, delete user preferences
  - Cannot add duplicate preference

**Total: 34 service tests**

### 3. `users/tests.py` - Main Entry Point
Imports and exposes all test classes from both test files.

## Test Results

**Ran 55 tests in 9.945s**

### Passing Tests: 40/55 ✅
### Failing Tests: 15/55 ❌

---

## 🔴 Errors to Fix (Priority Order)

### 1. **Chat Auto-Creation Signal Issue** (7 errors - HIGH PRIORITY)
**Error**: `UNIQUE constraint failed: users_chat.match_id`

**Root Cause**:
- A Django signal automatically creates a `Chat` when a `Match` is created
- Tests try to create another chat for the same match → UNIQUE constraint violation

**Affected Tests**:
- `test_cannot_send_message_to_other_user_chat`
- `test_create_chat`
- `test_get_chat_detail`
- `test_list_chats`
- `test_list_messages`
- `test_messages_ordered_by_sent_at`
- `test_send_message`

**Fix**:
```python
# In tests_services.py, ChatAndMessageAPITests.setUp()
# CHANGE FROM:
self.chat = Chat.objects.create(match=self.match)

# CHANGE TO:
self.chat = Chat.objects.get(match=self.match)  # Get auto-created chat
```

---

### 2. **Quest Required Field Missing** (4 errors - HIGH PRIORITY)
**Error**: `NOT NULL constraint failed: users_quests.quest_date`

**Root Cause**:
- `quest_date` field is required (NOT NULL) in the Quests model
- Tests don't provide it when creating Quest objects

**Affected Tests**:
- `test_delete_quest`
- `test_list_quests`
- `test_update_quest`
- `test_create_quest` (also fails with 400)

**Fix**:
```python
# Add quest_date to all Quest.objects.create() calls
from django.utils import timezone

Quests.objects.create(
    match=self.match,
    location_name='Quest 1',
    activity='Activity 1',
    quest_date=timezone.now() + timedelta(days=1)  # ADD THIS
)
```

---

### 3. **UserModeSettings URL Mismatch** (2 failures - MEDIUM PRIORITY)
**Error**: `404 Not Found`

**Root Cause**:
- Test uses `/api/user-mode-settings/`
- Actual URL might be `/api/settings/`

**Affected Tests**:
- `test_get_or_create_settings`
- `test_update_settings`

**Fix**: Check `users/urls.py` for correct URL pattern, then update tests:
```python
# Change from:
self.settings_url = '/api/user-mode-settings/'

# Change to (probably):
self.settings_url = '/api/settings/'
```

---

### 4. **Match Status Value Mismatch** (1 failure - LOW PRIORITY)
**Error**: `AssertionError: 'successful' != 'active'`

**Root Cause**:
- Match model default status is `'successful'`
- Test expects `'active'`

**Affected Tests**:
- `test_create_match`

**Fix**: Either update test or change model default:
```python
# Option 1: Update test expectation
self.assertEqual(response.data['status'], 'successful')

# Option 2: Or check Match model status field choices
```

---

### 5. **Match Update Validation Error** (1 failure - MEDIUM PRIORITY)
**Error**: `AssertionError: 400 != 200`

**Root Cause**:
- MatchSerializer validation fails when updating
- Likely due to `user2_id` being required but not provided in partial update

**Affected Tests**:
- `test_update_match`

**Fix**: Provide all required fields or make update truly partial:
```python
# Update test to include user2_id
data = {
    'status': 'completed',
    'user1_rating': 5,
    'user2_id': self.user2.id  # ADD THIS
}

# OR use PATCH instead of PUT
response = self.client.patch(url, data, format='json')
```

---

## ✅ Quick Fix Checklist

1. ✅ **Fix Chat signal issue** - Change `Chat.objects.create()` to `Chat.objects.get()` in setUp
2. ✅ **Add quest_date** - Add `quest_date=timezone.now() + timedelta(days=1)` to all Quest creates
3. ✅ **Fix settings URL** - Check urls.py and update test URL to `/api/settings/`
4. ✅ **Fix match status** - Change test expectation to `'successful'`
5. ✅ **Fix match update** - Add `user2_id` or use PATCH instead of PUT

## How to Run Tests

### Run all tests:
```bash
poetry run python manage.py test users
```

### Run only authentication tests:
```bash
poetry run python manage.py test users.tests_auth
```

### Run only service tests:
```bash
poetry run python manage.py test users.tests_services
```

### Run a specific test class:
```bash
poetry run python manage.py test users.tests_auth.UserRegistrationTests
```

### Run a specific test:
```bash
poetry run python manage.py test users.tests_auth.UserRegistrationTests.test_register_with_email_only
```

### Run with verbose output:
```bash
poetry run python manage.py test users --verbosity=2
```

## Next Steps

1. Fix Chat auto-creation issue in tests
2. Add required `quest_date` field to Quest test data
3. Update URL patterns or test URLs for UserModeSettings
4. Review 401 vs 403 status code behavior (may be correct DRF behavior)
5. Check Match status field values ('successful' vs 'active')
6. Add more edge case tests as needed
