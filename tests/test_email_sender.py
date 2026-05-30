import pytest
from unittest.mock import patch
from utils.email_sender import is_valid_email, resolve_recipients
from app import app

# Fixture to provide the Flask application context
@pytest.fixture
def app_context():
    with app.app_context():
        yield

# ---------------------------------------------------------
# Safe Dummy Classes to mimic SQLAlchemy behavior
# ---------------------------------------------------------
class DummyGroupMember:
    def __init__(self, usn, email):
        self.usn = usn
        self.email = email

# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

# 1. Pure Function Test (No Mocking Required)
def test_is_valid_email():
    # Valid emails
    assert is_valid_email("admin@bmsit.in") is True
    assert is_valid_email("student.name@domain.com") is True
    
    # Invalid emails
    assert is_valid_email("invalid-email-format") is False
    assert is_valid_email("missing@domain") is False


# 2. Database Logic Test (Requires Mocking)
@patch('utils.email_sender.Group')
@patch('utils.email_sender.GroupMember')
def test_resolve_recipients_mixed_input(mock_group_member, mock_group, app_context):
    # ARRANGE: Simulate the database finding our specific USN
    mock_member = DummyGroupMember("1BM24MC001", "student@bmsit.in")
    mock_group_member.query.filter_by.return_value.first.return_value = mock_member

    # ACT: Feed the function a mixed list (One direct email + One USN)
    input_list = ["direct@gmail.com", "1BM24MC001"]
    resolved = resolve_recipients(input_list)

    # ASSERT: The function should correctly process both types and return a length of 2
    assert len(resolved) == 2
    assert "direct@gmail.com" in resolved
    assert "1BM24MC001" in resolved