"""
Example code with various issues for testing the code review system
This file intentionally contains bugs and code smells for demonstration
"""

# TODO: Refactor this entire module

def calculate_sum(x, y):
    """Calculate sum without validation"""
    result = x + y
    print(result)  # Debug statement
    return result

def get_user_data(user_ids):
    """
    Fetches user data - has N+1 query problem
    """
    users = []
    for id in user_ids:
        # This creates N queries instead of 1
        user = database.query(f"SELECT * FROM users WHERE id={id}")  # SQL injection risk!
        users.append(user)
    return users

def process_file(filename):
    # Missing error handling
    f = open(filename, 'r')
    content = f.read()
    return content

def complex_function(a, b, c, d, e):
    """Function with too many parameters and high complexity"""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return True
    return False

class UserManager:
    def __init__(self):
        self.api_key = "sk-1234567890abcdef"  # Hardcoded secret!
        
    def authenticate(self, password):
        # Weak authentication
        return password == "admin123"
    
    def get_users(self):
        # No pagination, could load millions of records
        return User.objects.all()

# Short variable names
x = 10
y = 20
z = x + y

# Unused imports
import os
import sys
import random

# Dead code
def unused_function():
    """This is never called"""
    pass

# Missing docstrings
def mystery_function(param):
    return param * 2

# Inefficient loop
items = range(1000)
result = []
for item in items:
    for i in range(1000):
        result.append(item * i)  # O(n²) complexity

# No input validation
def divide(a, b):
    return a / b  # Will crash if b is 0

# Magic numbers
def calculate_discount(price):
    if price > 100:
        return price * 0.9  # What is 0.9? Use named constant
    return price

# Missing type hints
def process_data(data):
    return [item.upper() for item in data]

# Global variables
GLOBAL_COUNTER = 0

def increment():
    global GLOBAL_COUNTER
    GLOBAL_COUNTER += 1
