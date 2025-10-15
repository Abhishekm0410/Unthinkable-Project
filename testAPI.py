import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Sample test code
SAMPLE_PYTHON_CODE = '''
def calculate_sum(x, y):
    # TODO: Add input validation
    result = x + y
    print(result)
    return result

def process_users():
    users = get_users()
    for user in users:
        data = db.query(user.id)  # N+1 query problem
        process(data)
'''

SAMPLE_JAVASCRIPT_CODE = '''
function fetchData() {
    // Missing error handling
    const response = fetch('/api/data');
    const data = response.json();
    return data;
}

for (let i = 0; i < items.length; i++) {
    for (let j = 0; j < items[i].length; j++) {
        console.log(items[i][j]);
    }
}
'''

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "endpoints" in response.json()

class TestCodeReview:
    """Test code review functionality"""
    
    def test_review_python_code(self):
        """Test reviewing Python code"""
        response = client.post(
            "/api/review",
            json={
                "code": SAMPLE_PYTHON_CODE,
                "language": "python",
                "filename": "test.py"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "review_id" in data
        assert "score" in data
        assert "priority" in data
        assert isinstance(data["priority"], list)
        assert len(data["priority"]) > 0
        
        # Check issue structure
        issue = data["priority"][0]
        assert "severity" in issue
        assert "title" in issue
        assert "description" in issue
        assert "line" in issue
        assert "suggestion" in issue
    
    def test_review_javascript_code(self):
        """Test reviewing JavaScript code"""
        response = client.post(
            "/api/review",
            json={
                "code": SAMPLE_JAVASCRIPT_CODE,
                "language": "javascript",
                "filename": "test.js"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] >= 0 and data["score"] <= 100
    
    def test_review_empty_code(self):
        """Test with empty code"""
        response = client.post(
            "/api/review",
            json={
                "code": "",
                "language": "python"
            }
        )
        # Should still return a response
        assert response.status_code in [200, 400]
    
    def test_review_invalid_language(self):
        """Test with invalid language"""
        response = client.post(
            "/api/review",
            json={
                "code": "test code",
                "language": "invalid_lang"
            }
        )
        # Should handle gracefully
        assert response.status_code in [200, 400]

class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_python_file(self):
        """Test uploading a Python file"""
        files = {
            "file": ("test.py", SAMPLE_PYTHON_CODE, "text/plain")
        }
        response = client.post("/api/review/file", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "review_id" in data
    
    def test_upload_javascript_file(self):
        """Test uploading a JavaScript file"""
        files = {
            "file": ("test.js", SAMPLE_JAVASCRIPT_CODE, "text/plain")
        }
        response = client.post("/api/review/file", files=files)
        assert response.status_code == 200

class TestChatEndpoint:
    """Test chat functionality"""
    
    def test_chat_basic_question(self):
        """Test basic chat question"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Why is this slow?",
                "code_context": SAMPLE_PYTHON_CODE
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
    
    def test_chat_without_context(self):
        """Test chat without code context"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Hello"
            }
        )
        assert response.status_code == 200
    
    def test_chat_explain_code(self):
        """Test explain code question"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Explain this",
                "code_context": SAMPLE_JAVASCRIPT_CODE
            }
        )
        assert response.status_code == 200

class TestTeamInsights:
    """Test team insights endpoint"""
    
    def test_get_team_insights(self):
        """Test getting team insights"""
        response = client.get("/api/team-insights/default")
        assert response.status_code == 200
        data = response.json()
        
        assert "team_id" in data
        assert "total_reviews" in data
        assert "common_patterns" in data
        assert "common_issues" in data
    
    def test_get_custom_team_insights(self):
        """Test getting custom team insights"""
        response = client.get("/api/team-insights/my-team")
        assert response.status_code == 200

class TestReviewRetrieval:
    """Test review retrieval and management"""
    
    def test_list_reviews(self):
        """Test listing reviews"""
        response = client.get("/api/reviews")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "reviews" in data
    
    def test_list_reviews_with_limit(self):
        """Test listing reviews with limit"""
        response = client.get("/api/reviews?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) <= 5

class TestIssueDetection:
    """Test specific issue detection"""
    
    def test_detect_todo_comments(self):
        """Test TODO comment detection"""
        code_with_todo = "# TODO: Fix this\ndef test(): pass"
        response = client.post(
            "/api/review",
            json={
                "code": code_with_todo,
                "language": "python"
            }
        )
        assert response.status_code == 200
        issues = response.json()["priority"]
        todo_issues = [i for i in issues if "TODO" in i["title"]]
        assert len(todo_issues) > 0
    
    def test_detect_print_statements(self):
        """Test print statement detection"""
        code_with_print = "print('debug')\ndef test(): pass"
        response = client.post(
            "/api/review",
            json={
                "code": code_with_print,
                "language": "python"
            }
        )
        assert response.status_code == 200
        issues = response.json()["priority"]
        debug_issues = [i for i in issues if "Debug" in i["title"]]
        assert len(debug_issues) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
