"""
Test Suite for CUPID Users App
==============================

This directory contains comprehensive tests for the CUPID dating app's users application.

## Test Files Overview

### 1. test_models.py
Tests for all Django models in the users app.

**Classes:**
- UserModelTests: Tests for User model
- UserProfileTests: Tests for UserProfile model
- UserModeSettingsTests: Tests for UserModeSettings model
- PreferenceTests: Tests for Preference model
- UserPreferenceTests: Tests for UserPreference model
- MatchTests: Tests for Match model
- QuestTests: Tests for Quests model
- ChatTests: Tests for Chat model
- MessageTests: Tests for Message model
- TaskTests: Tests for Task model
- ExpiringTokenTests: Tests for ExpiringToken model

**Key Test Scenarios:**
- Model creation and field validation
- Relationships (OneToOne, ForeignKey, ManyToMany)
- Default values and constraints
- Cascade delete behavior
- Timestamps and metadata

### 2. test_auth_views.py
Tests for authentication endpoints (register, login, logout, tokens).

**Classes:**
- UserRegistrationTests: Registration endpoint tests
- UserLoginTests: Login endpoint tests
- UserLogoutTests: Logout endpoint tests
- TokenListTests: Token management endpoint tests

**Test Scenarios:**
- Registration with email/phone
- Login with email/phone
- Password validation
- Duplicate account prevention
- Profile creation during registration
- Token generation and expiration
- Logout and token revocation
- Age verification (13+)
- URL validation for photos/videos

### 3. test_profile_views.py
Tests for user profile endpoints.

**Classes:**
- ProfileViewTests: User's own profile management
- UserPublicProfileTests: Viewing other users' profiles
- ProfileSerializerTests: Profile serializer validation

**Test Scenarios:**
- Get own profile
- Update profile information
- Partial profile updates
- Location-based data
- Access control for matched users only
- Read-only field enforcement

### 4. test_preference_views.py
Tests for user preference/interest management.

**Classes:**
- PreferenceListTests: Preference list and creation
- UserPreferenceListTests: User preference management
- UserPreferenceDestroyTests: Removing preferences
- PreferenceSerializerTests: Serializer validation

**Test Scenarios:**
- List all preferences
- Create new preferences
- Add preferences to user
- Remove preferences from user
- Duplicate preference handling
- Preference ordering

### 5. test_match_views.py
Tests for matching functionality.

**Classes:**
- MatchListTests: Match listing and creation
- MatchDetailTests: Individual match management
- MatchWithUserViewTests: Quick match creation
- QuestListTests: Quest listing and creation
- QuestDetailTests: Individual quest management
- QuestHintViewTests: Posting hints for quests
- MatchRatingViewTests: Rating matches

**Test Scenarios:**
- Create matches between users
- View match details
- Update match status
- Create quests for matches
- Post hints from both users
- Rate matches (1-5)
- Access control for match participants
- Unique constraint enforcement (match, location_name)

### 6. test_chat_views.py
Tests for chat and messaging functionality.

**Classes:**
- ChatListTests: Chat listing and creation
- ChatDetailTests: Individual chat management
- MessageListTests: Message listing and sending
- MessageDetailTests: Individual message management
- ChatSerializerTests: Chat serializer validation
- MessageSerializerTests: Message serializer validation

**Test Scenarios:**
- Create chats for matches
- Send messages
- List message history
- Message ordering by time
- Access control for chat participants
- Delete messages and chats
- Automatic sender assignment
- Long message handling

### 7. test_task_views.py
Tests for task management and user settings.

**Classes:**
- TaskListTests: Task listing and creation
- TaskDetailTests: Individual task management
- UserModeSettingsTests: User settings management
- TaskSerializerTests: Task serializer validation
- UserModeSettingsSerializerTests: Settings serializer validation

**Test Scenarios:**
- Create and manage tasks
- Schedule tasks with start/end times
- Free time tasks
- Ghost mode settings
- Location sharing preferences
- Notification preferences
- Partial updates
- Default settings values

### 8. test_utils.py
Utility classes and factories for test data creation.

**Factories:**
- UserFactory: Create test users with profiles
- PreferenceFactory: Create preferences and assign to users
- MatchFactory: Create matches between users
- QuestFactory: Create quests for matches
- MessageFactory: Create chats with messages
- TaskFactory: Create tasks with various configurations
- AuthTestMixin: Helper for authentication testing

**Utility Functions:**
- create_test_data_set(): Creates comprehensive test dataset

**Usage Examples:**
```python
# Create user with token
user, token, token_obj = UserFactory.create_user_with_token(email='test@example.com')

# Create preferences
prefs = PreferenceFactory.create_preferences(['Books', 'Gym'])
PreferenceFactory.assign_preferences(user, prefs)

# Create match with chat
match, chat = MatchFactory.create_match_with_chat(user1, user2)

# Create chat with messages
chat, messages = MessageFactory.create_chat_with_messages(user1, user2, message_count=5)
```

### 9. test_integration.py
High-level integration tests for complete workflows.

**Test Classes:**
- UserRegistrationAndLoginIntegrationTests: Full auth flow
- MatchAndQuestIntegrationTests: Matching and quest workflow
- ChatAndMessagingIntegrationTests: Messaging workflows
- PreferencesAndMatchingIntegrationTests: Preferences in matching
- TaskAndSettingsIntegrationTests: Task and settings workflows
- CompleteUserJourneyIntegrationTests: End-to-end scenarios

**Test Scenarios:**
- Complete registration → login → profile update flow
- Match creation → quest creation → hint posting → rating flow
- Chat creation → messaging → message history flow
- Preference management with matching
- Task scheduling and management
- End-to-end user journey from registration to matching

## Running Tests

### Run all tests in the test/users/ directory:
```bash
python manage.py test test.users
```

### Run specific test file:
```bash
python manage.py test test.users.test_models
python manage.py test test.users.test_auth_views
```

### Run specific test class:
```bash
python manage.py test test.users.test_models.UserModelTests
```

### Run specific test method:
```bash
python manage.py test test.users.test_models.UserModelTests.test_create_user_with_email
```

### Run with verbosity:
```bash
python manage.py test test.users -v 2
```

### Run with coverage:
```bash
coverage run --source='users' manage.py test test.users
coverage report
coverage html
```

## Test Coverage

The test suite covers:
- All model creation and validation
- All API endpoints (GET, POST, PUT, DELETE)
- Authentication and authorization
- Error handling and edge cases
- Relationship enforcement
- Data validation
- Serializer behavior
- Access control
- Complete user workflows

## API Endpoints Tested

### Authentication
- POST /api/auth/register/ - User registration
- POST /api/auth/login/ - User login
- POST /api/auth/logout/ - User logout
- GET /api/auth/tokens/ - List user tokens

### Profile
- GET /api/profile/ - Get own profile
- PUT /api/profile/ - Update own profile
- GET /api/profile/<user_id>/ - Get other user's profile (matched only)

### Preferences
- GET /api/preferences/ - List all preferences
- POST /api/preferences/ - Create preference
- GET /api/user-preferences/ - List user's preferences
- POST /api/user-preferences/ - Add preference to user
- DELETE /api/user-preferences/<pref_id>/ - Remove preference

### Matches
- GET /api/matches/ - List user's matches
- POST /api/matches/ - Create match
- GET /api/matches/<match_id>/ - Get match detail
- PUT /api/matches/<match_id>/ - Update match
- DELETE /api/matches/<match_id>/ - Delete match
- PUT /api/matches/with/<user_id>/ - Create/get match with user
- POST /api/matches/<match_id>/rate/ - Rate match

### Quests
- GET /api/quests/ - List user's quests
- POST /api/quests/ - Create quest
- GET /api/quests/<quest_id>/ - Get quest detail
- PUT /api/quests/<quest_id>/ - Update quest
- DELETE /api/quests/<quest_id>/ - Delete quest
- POST /api/quests/<quest_id>/hint/ - Post hint for quest

### Chat & Messages
- GET /api/chats/ - List user's chats
- POST /api/chats/ - Create chat
- GET /api/chats/<chat_id>/ - Get chat detail
- PUT /api/chats/<chat_id>/ - Update chat
- DELETE /api/chats/<chat_id>/ - Delete chat
- GET /api/chats/<chat_id>/messages/ - List messages in chat
- POST /api/chats/<chat_id>/messages/ - Send message
- GET /api/messages/<msg_id>/ - Get message detail
- DELETE /api/messages/<msg_id>/ - Delete message

### Tasks & Settings
- GET /api/tasks/ - List user's tasks
- POST /api/tasks/ - Create task
- GET /api/tasks/<task_id>/ - Get task detail
- PUT /api/tasks/<task_id>/ - Update task
- DELETE /api/tasks/<task_id>/ - Delete task
- GET /api/settings/ - Get user settings
- PUT /api/settings/ - Update user settings

## Test Data Fixtures

Tests use factories to generate realistic data:
- Users with email/phone authentication
- Profiles with location data
- Preferences and interests
- Matches with various statuses
- Quests with locations and hints
- Chat conversations with messages
- Tasks with schedules
- Tokens with expiration

## Key Testing Patterns

### 1. Authentication Testing
```python
# Create user and token
user, token, _ = UserFactory.create_user_with_token(email='test@example.com')

# Use token for requests
self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
response = self.client.get('/api/profile/')
```

### 2. Access Control Testing
```python
# Verify only match participants can view
self.assertFalse(Match.objects.filter(user1=user, user2=target).exists())
response = self.client.get(f'/api/profile/{target.id}/')
self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

### 3. Data Validation Testing
```python
# Test invalid input
data = {'rating': 6}  # Invalid: must be 1-5
response = self.client.post(f'/api/matches/{match.id}/rate/', data)
self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

### 4. Relationship Testing
```python
# Verify cascade delete
user.delete()
messages = Message.objects.filter(sender=user)
self.assertEqual(messages.count(), 0)
```

## Best Practices

1. **Use Factories**: Use UserFactory, PreferenceFactory, etc. for consistent test data
2. **Test One Thing**: Each test method should test one specific behavior
3. **Clear Names**: Test names clearly describe what is being tested
4. **Assertions**: Use specific assertions (assertEqual, assertTrue, etc.)
5. **Cleanup**: Django TestCase handles cleanup automatically
6. **Mocking**: Use mocking for external services (if needed)
7. **Edge Cases**: Test boundary conditions and error cases

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external service dependencies (except Django ORM)
- In-memory database or test database
- Deterministic results
- Fast execution
- Clear failure messages

## Contributing Tests

When adding new features:
1. Write tests first (TDD approach)
2. Use existing factories for consistency
3. Follow naming conventions: test_<feature>_<scenario>
4. Add docstrings explaining the test
5. Keep tests isolated and independent
6. Update this README with new test files
"""
