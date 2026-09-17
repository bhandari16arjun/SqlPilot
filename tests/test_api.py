import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

@patch("app.api.graph.stream")
@patch("app.api.graph.get_state")
def test_query_endpoint_success(mock_get_state, mock_stream):
    # Mock stream to just yield nothing
    mock_stream.return_value = []
    
    # Mock the state returned by get_state
    mock_state = MagicMock()
    mock_state.next = []
    mock_state.values = {
        "generated_sql": "SELECT 1;",
        "execution_results": [{"1": 1}],
        "final_answer": "This is a test."
    }
    mock_get_state.return_value = mock_state
    
    response = client.post("/query", json={"question": "test?", "thread_id": "123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sql"] == "SELECT 1;"
    assert data["explanation"] == "This is a test."

@patch("app.api.graph.stream")
@patch("app.api.graph.get_state")
def test_query_endpoint_needs_clarification(mock_get_state, mock_stream):
    mock_stream.return_value = []
    
    mock_state = MagicMock()
    mock_state.next = ["clarify"]
    mock_state.values = {
        "clarification_question": "Did you mean A or B?"
    }
    mock_get_state.return_value = mock_state
    
    response = client.post("/query", json={"question": "test?", "thread_id": "123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_clarification"
    assert data["message"] == "Did you mean A or B?"

@patch("app.api.graph.stream")
@patch("app.api.graph.get_state")
@patch("app.api.graph.update_state")
def test_resume_endpoint(mock_update_state, mock_get_state, mock_stream):
    mock_stream.return_value = []
    
    # State before resume
    mock_state = MagicMock()
    mock_state.next = ["clarify"]
    mock_state.values = {
        "conversation_history": [],
        "clarification_question": "Did you mean A or B?",
        "generated_sql": "SELECT 2;",
        "execution_results": [],
        "final_answer": "Resumed answer."
    }
    mock_get_state.return_value = mock_state
    
    response = client.post("/resume", json={"answer": "I meant A", "thread_id": "123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["explanation"] == "Resumed answer."
    assert mock_update_state.called
