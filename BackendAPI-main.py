from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import openai
import os
from datetime import datetime
import json
import re
from pathlib import Path

app = FastAPI(title="Smart Code Review API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# In-memory storage (replace with database in production)
reviews_db = {}
team_context_db = {
    "reviews_count": 0,
    "common_patterns": [],
    "common_issues": {},
    "team_preferences": {}
}

# Models
class CodeReviewRequest(BaseModel):
    code: str
    language: str
    filename: Optional[str] = "untitled"
    team_id: Optional[str] = "default"

class ChatRequest(BaseModel):
    message: str
    code_context: Optional[str] = ""
    review_id: Optional[str] = None

class Issue(BaseModel):
    id: int
    severity: str
    title: str
    description: str
    line: int
    impact: str
    fix_time: str
    business_impact: str
    suggestion: str
    auto_fix_available: bool
    code_snippet: Optional[str] = None

class ReviewResponse(BaseModel):
    review_id: str
    score: int
    improvement: str
    priority: List[Issue]
    metrics: Dict[str, str]
    team_insights: List[str]
    timestamp: str

# Helper Functions
def detect_language(filename: str, code: str) -> str:
    """Auto-detect programming language"""
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.jsx': 'javascript',
        '.ts': 'typescript', '.tsx': 'typescript', '.java': 'java',
        '.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rb': 'ruby',
        '.php': 'php', '.cs': 'csharp', '.swift': 'swift'
    }
    
    ext = Path(filename).suffix.lower()
    if ext in ext_map:
        return ext_map[ext]
    
    # Fallback: detect from code patterns
    if 'def ' in code and 'import ' in code:
        return 'python'
    elif 'function ' in code or 'const ' in code:
        return 'javascript'
    
    return 'unknown'

def analyze_code_complexity(code: str) -> Dict[str, any]:
    """Analyze code complexity metrics"""
    lines = code.split('\n')
    non_empty_lines = [l for l in lines if l.strip()]
    
    # Count nesting levels
    max_nesting = 0
    current_nesting = 0
    for line in lines:
        indent = len(line) - len(line.lstrip())
        current_nesting = indent // 4  # Assuming 4-space indentation
        max_nesting = max(max_nesting, current_nesting)
    
    # Count loops and conditionals
    control_structures = len(re.findall(r'\b(if|for|while|switch|case)\b', code))
    
    return {
        'total_lines': len(lines),
        'code_lines': len(non_empty_lines),
        'max_nesting': max_nesting,
        'control_structures': control_structures,
        'complexity_score': min(100, (max_nesting * 10) + (control_structures * 2))
    }

def generate_llm_review(code: str, language: str, team_context: Dict) -> Dict:
    """Use LLM to analyze code and generate review"""
    
    prompt = f"""You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.

Analyze this {language} code and provide a comprehensive review:

```{language}
{code}
```

Team Context:
- Previous reviews: {team_context.get('reviews_count', 0)}
- Common patterns: {', '.join(team_context.get('common_patterns', []))}

Please provide:
1. **Critical Issues** (High Severity): Security vulnerabilities, performance bottlenecks, potential crashes
2. **Important Issues** (Medium Severity): Code quality, maintainability, missing error handling
3. **Minor Issues** (Low Severity): Style improvements, naming conventions, documentation

For EACH issue found, provide:
- Line number (estimate if needed)
- Clear description of the problem
- Business impact (how it affects users/system)
- Specific fix suggestion
- Estimated fix time

Also provide:
- Overall code quality score (0-100)
- Metrics: Complexity, Maintainability, Security, Performance (rate as: Excellent, Good, Medium, Poor)
- Team-specific insights based on common patterns

Format your response as JSON with this structure:
{{
  "score": 75,
  "issues": [
    {{
      "severity": "high|medium|low",
      "title": "Issue title",
      "description": "Detailed description",
      "line": 45,
      "impact": "High|Medium|Low",
      "fix_time": "30 min",
      "business_impact": "Could slow down user dashboard",
      "suggestion": "Specific fix recommendation",
      "auto_fix_available": true
    }}
  ],
  "metrics": {{
    "complexity": "Good",
    "maintainability": "Medium",
    "security": "Poor",
    "performance": "Good"
  }},
  "team_insights": ["Insight 1", "Insight 2"]
}}
"""

    try:
        # Using OpenAI GPT-4 (replace with your preferred LLM)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback to rule-based analysis
        return generate_fallback_review(code, language)

def generate_fallback_review(code: str, language: str) -> Dict:
    """Fallback rule-based analysis if LLM fails"""
    issues = []
    issue_id = 1
    
    lines = code.split('\n')
    
    # Check for common issues
    for i, line in enumerate(lines, 1):
        # Check for TODO/FIXME
        if 'TODO' in line or 'FIXME' in line:
            issues.append({
                "severity": "low",
                "title": "Unresolved TODO/FIXME",
                "description": f"Line {i} contains unresolved TODO or FIXME comment",
                "line": i,
                "impact": "Low",
                "fix_time": "5 min",
                "business_impact": "Code maintainability",
                "suggestion": "Address the TODO or create a ticket to track it",
                "auto_fix_available": False
            })
        
        # Check for print/console.log statements
        if re.search(r'\b(print|console\.log)\(', line):
            issues.append({
                "severity": "low",
                "title": "Debug Statement Found",
                "description": f"Line {i} contains a print/log statement that should be removed",
                "line": i,
                "impact": "Low",
                "fix_time": "1 min",
                "business_impact": "Production logs pollution",
                "suggestion": "Remove debug statement or use proper logging",
                "auto_fix_available": True
            })
        
        # Check for short variable names
        if re.search(r'\b[a-z]\s*=\s*', line) and 'for' not in line:
            issues.append({
                "severity": "low",
                "title": "Non-descriptive Variable Name",
                "description": f"Line {i} uses a single-letter variable name",
                "line": i,
                "impact": "Low",
                "fix_time": "2 min",
                "business_impact": "Code readability",
                "suggestion": "Use a descriptive variable name",
                "auto_fix_available": False
            })
        
        # Check for missing error handling
        if 'try:' in line:
            try_index = i
            has_except = False
            for j in range(i, min(i+20, len(lines))):
                if 'except' in lines[j]:
                    has_except = True
                    break
            if not has_except:
                issues.append({
                    "severity": "medium",
                    "title": "Incomplete Error Handling",
                    "description": f"Line {i} has try block without except clause",
                    "line": i,
                    "impact": "Medium",
                    "fix_time": "10 min",
                    "business_impact": "Potential unhandled exceptions",
                    "suggestion": "Add except clause with proper error handling",
                    "auto_fix_available": True
                })
    
    complexity = analyze_code_complexity(code)
    score = max(50, 100 - complexity['complexity_score'])
    
    return {
        "score": score,
        "issues": issues[:10],  # Limit to top 10
        "metrics": {
            "complexity": "Medium" if complexity['complexity_score'] < 50 else "High",
            "maintainability": "Good",
            "security": "Needs Review",
            "performance": "Good"
        },
        "team_insights": [
            "Consider adding more comments for complex logic",
            "Follow consistent naming conventions",
            "Add unit tests for critical functions"
        ]
    }

def calculate_improvement(current_score: int, team_id: str) -> str:
    """Calculate improvement from previous reviews"""
    # In production, fetch from database
    previous_avg = 70  # Mock previous score
    diff = current_score - previous_avg
    return f"+{diff}" if diff > 0 else str(diff)

# API Endpoints
@app.get("/")
def root():
    return {
        "message": "Smart Code Review API",
        "version": "1.0.0",
        "endpoints": ["/review", "/chat", "/team-insights", "/health"]
    }

@app.post("/api/review", response_model=ReviewResponse)
async def review_code(request: CodeReviewRequest, background_tasks: BackgroundTasks):
    """Main endpoint to review code"""
    
    try:
        # Get team context
        team_context = team_context_db.copy()
        
        # Analyze code with LLM
        llm_result = generate_llm_review(request.code, request.language, team_context)
        
        # Generate review ID
        review_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Format issues
        issues = []
        for idx, issue in enumerate(llm_result.get('issues', []), 1):
            issues.append(Issue(
                id=idx,
                severity=issue.get('severity', 'low'),
                title=issue.get('title', 'Unknown Issue'),
                description=issue.get('description', ''),
                line=issue.get('line', 1),
                impact=issue.get('impact', 'Low'),
                fix_time=issue.get('fix_time', '10 min'),
                business_impact=issue.get('business_impact', 'Minor impact'),
                suggestion=issue.get('suggestion', 'Review and fix'),
                auto_fix_available=issue.get('auto_fix_available', False)
            ))
        
        # Calculate score and improvement
        score = llm_result.get('score', 75)
        improvement = calculate_improvement(score, request.team_id)
        
        # Create review response
        review = ReviewResponse(
            review_id=review_id,
            score=score,
            improvement=improvement,
            priority=issues,
            metrics=llm_result.get('metrics', {
                "complexity": "Medium",
                "maintainability": "Good",
                "security": "Good",
                "performance": "Good"
            }),
            team_insights=llm_result.get('team_insights', [
                "Code follows team conventions",
                "Consider adding more test coverage"
            ]),
            timestamp=datetime.now().isoformat()
        )
        
        # Store review
        reviews_db[review_id] = review.dict()
        
        # Update team context in background
        background_tasks.add_task(update_team_context, request.team_id, review)
        
        return review
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")

@app.post("/api/review/file")
async def review_file(file: UploadFile = File(...), team_id: str = "default"):
    """Upload and review a code file"""
    
    try:
        # Read file content
        content = await file.read()
        code = content.decode('utf-8')
        
        # Detect language
        language = detect_language(file.filename, code)
        
        # Create review request
        request = CodeReviewRequest(
            code=code,
            language=language,
            filename=file.filename,
            team_id=team_id
        )
        
        # Review code
        return await review_code(request, BackgroundTasks())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/api/chat")
async def chat_with_code(request: ChatRequest):
    """Chat interface for code questions"""
    
    try:
        prompt = f"""You are a helpful code assistant. Answer the user's question about their code.

User Question: {request.message}

Code Context:
```
{request.code_context[:500]}  # Limit context
```

Provide a clear, concise answer. If suggesting fixes, provide code examples.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert code assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        return {
            "response": answer,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fallback responses
        fallback_responses = {
            "why is this slow": "I see potential performance issues. Look for nested loops, repeated database queries, or inefficient algorithms. Consider using caching or optimizing data structures.",
            "explain this": "This code appears to process data. To give you a detailed explanation, I'd need to analyze the specific logic and data flow.",
            "how to fix": "To fix this, consider: 1) Refactoring complex functions, 2) Adding error handling, 3) Optimizing loops and queries, 4) Adding input validation."
        }
        
        answer = fallback_responses.get(
            request.message.lower(), 
            "I can help explain code, suggest improvements, or answer questions. Try asking specific questions about performance, bugs, or best practices."
        )
        
        return {
            "response": answer,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/team-insights/{team_id}")
async def get_team_insights(team_id: str):
    """Get team-specific insights and metrics"""
    
    return {
        "team_id": team_id,
        "total_reviews": team_context_db.get('reviews_count', 0),
        "average_score": 78,
        "improvement": "+5",
        "common_patterns": team_context_db.get('common_patterns', [
            "Async/await for asynchronous code",
            "Jest for testing",
            "Redux for state management"
        ]),
        "common_issues": {
            "missing_error_handling": 12,
            "inefficient_queries": 8,
            "poor_naming": 15,
            "missing_tests": 6
        },
        "top_improvements": [
            "Added error handling in 23 functions",
            "Optimized 15 database queries",
            "Improved test coverage by 18%"
        ]
    }

@app.get("/api/review/{review_id}")
async def get_review(review_id: str):
    """Retrieve a specific review"""
    
    if review_id not in reviews_db:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return reviews_db[review_id]

@app.delete("/api/review/{review_id}")
async def delete_review(review_id: str):
    """Delete a review"""
    
    if review_id not in reviews_db:
        raise HTTPException(status_code=404, detail="Review not found")
    
    del reviews_db[review_id]
    return {"message": "Review deleted successfully"}

@app.get("/api/reviews")
async def list_reviews(limit: int = 10, team_id: str = "default"):
    """List recent reviews"""
    
    reviews = list(reviews_db.values())[-limit:]
    return {
        "total": len(reviews_db),
        "reviews": reviews
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_reviews": len(reviews_db)
    }

# Background task
def update_team_context(team_id: str, review: ReviewResponse):
    """Update team context based on review"""
    team_context_db['reviews_count'] += 1
    
    # Extract patterns from review
    for issue in review.priority:
        issue_type = issue.title.lower()
        if issue_type not in team_context_db.get('common_issues', {}):
            team_context_db.setdefault('common_issues', {})[issue_type] = 0
        team_context_db['common_issues'][issue_type] += 1

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
