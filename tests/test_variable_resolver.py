#tests/test_variable_resolver.py
import pytest
from unittest.mock import patch
from utils.variable_resolver import fetch_template_variables
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
    def __init__(self):
        self.usn = "1BM24MC001"
        self.group_id = "MCA2024"
        self.email = "test@bmsit.in"
        self._sa_instance_state = "ignore"

class DummyGroup:
    def __init__(self):
        self.group_id = "MCA2024"  # <--- Add this exact line
        self.name = "MCA 1st Year"
        self.description = "Batch of 2024-2026"
        self._sa_instance_state = "ignore"

# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------
@patch('utils.variable_resolver.Group')
@patch('utils.variable_resolver.GroupMember')
def test_fetch_template_variables_success(mock_group_member, mock_group, app_context):
    # 1. ARRANGE: Inject our safe dummy objects instead of MagicMocks
    mock_group_member.query.filter_by.return_value.first.return_value = DummyGroupMember()
    mock_group.query.filter_by.return_value.first.return_value = DummyGroup()

    # 2. ACT: Execute the actual function
    variables, error = fetch_template_variables("1BM24MC001")

    # 3. ASSERT: Verify the logic extracted data from the dummies correctly
    assert error is None
    assert variables is not None
    assert variables["usn"] == "1BM24MC001"
    assert variables["email"] == "test@bmsit.in"
    assert variables["class_name"] == "MCA 1st Year"
    assert variables["class_description"] == "Batch of 2024-2026"

@patch('utils.variable_resolver.GroupMember')
def test_fetch_template_variables_usn_not_found(mock_group_member, app_context):
    # ARRANGE: Simulate missing user
    mock_group_member.query.filter_by.return_value.first.return_value = None

    # ACT
    variables, error = fetch_template_variables("INVALID_USN")

    # ASSERT: The function should fail gracefully
    assert variables is None
    assert "not found" in error