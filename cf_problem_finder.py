import requests
import json
from typing import List, Set, Dict

class CFProblemFinder:
    def __init__(self):
        self.base_url = "https://codeforces.com/api"
        
    def get_user_submissions(self, username: str) -> Set[str]:
        """Get all problem IDs that a user has attempted."""
        url = f"{self.base_url}/user.status"
        params = {
            "handle": username,
            "count": 10000  # Get maximum submissions
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                raise Exception(f"API Error: {data['comment']}")
                
            # Extract problem IDs from submissions
            problem_ids = set()
            for submission in data["result"]:
                problem = submission["problem"]
                problem_id = f"{problem['contestId']}{problem['index']}"
                problem_ids.add(problem_id)
                
            return problem_ids
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching submissions for {username}: {e}")
            return set()
            
    def get_problems_by_rating(self, rating: int) -> List[Dict]:
        """Get all problems with the specified rating."""
        url = f"{self.base_url}/problemset.problems"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                raise Exception(f"API Error: {data['comment']}")
                
            # Filter problems by rating and contest ID > 1200
            problems = []
            for problem in data["result"]["problems"]:
                if problem.get("rating") == rating and problem.get("contestId", 0) > 1200:
                    problems.append(problem)
                    
            return problems
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching problems: {e}")
            return []
            
    def find_unsolved_problems(self, username1: str, username2: str, rating: int) -> List[Dict]:
        """Find problems that neither user has attempted with the specified rating."""
        # Get submissions for both users
        user1_submissions = self.get_user_submissions(username1)
        user2_submissions = self.get_user_submissions(username2)
        
        # Get all problems with the specified rating
        problems = self.get_problems_by_rating(rating)
        
        # Filter out problems that either user has attempted
        unsolved_problems = []
        for problem in problems:
            problem_id = f"{problem['contestId']}{problem['index']}"
            if problem_id not in user1_submissions and problem_id not in user2_submissions:
                unsolved_problems.append(problem)
                
        return unsolved_problems

def main():
    finder = CFProblemFinder()
    
    # Get input from user
    username1 = input("Enter first username: ")
    username2 = input("Enter second username: ")
    rating = int(input("Enter problem rating: "))
    
    # Find unsolved problems
    unsolved_problems = finder.find_unsolved_problems(username1, username2, rating)
    
    # Print results
    if unsolved_problems:
        print(f"\nFound {len(unsolved_problems)} unsolved problems with rating {rating}:")
        for problem in unsolved_problems:
            print(f"Problem {problem['contestId']}{problem['index']}: {problem['name']}")
    else:
        print(f"\nNo unsolved problems found with rating {rating}")

if __name__ == "__main__":
    main() 