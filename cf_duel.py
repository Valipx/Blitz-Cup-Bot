import requests
import time
import random
from typing import Dict, Set, Optional, List
from datetime import datetime

class CFDuel:
    def __init__(self, username1: str, username2: str, rating: int):
        self.base_url = "https://codeforces.com/api"
        self.username1 = username1
        self.username2 = username2
        self.rating = rating
        self.target_problem = None
        self.start_time = None
        self.last_submission_ids = {
            username1: self._get_latest_submission_id(username1),
            username2: self._get_latest_submission_id(username2)
        }
        print(f"Initial submission IDs - {username1}: {self.last_submission_ids[username1]}, {username2}: {self.last_submission_ids[username2]}")
        
    def _get_latest_submission_id(self, username: str) -> int:
        """Get the ID of the latest submission for a user."""
        url = f"{self.base_url}/user.status"
        params = {
            "handle": username,
            "count": 1
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK" or not data["result"]:
                return 0
                
            return data["result"][0]["id"]
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest submission for {username}: {e}")
            return 0
            
    def _get_user_submissions(self, username: str) -> Set[str]:
        """Get all problem IDs that a user has attempted."""
        url = f"{self.base_url}/user.status"
        params = {
            "handle": username,
            "count": 10000
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                return set()
                
            problem_ids = set()
            for submission in data["result"]:
                problem = submission["problem"]
                problem_id = f"{problem['contestId']}{problem['index']}"
                problem_ids.add(problem_id)
                
            return problem_ids
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching submissions for {username}: {e}")
            return set()
            
    def _get_problems_by_rating(self) -> List[Dict]:
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
                if problem.get("rating") == self.rating and problem.get("contestId", 0) > 1200:
                    problems.append(problem)
                    
            return problems
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching problems: {e}")
            return []
            
    def find_random_problem(self) -> Optional[Dict]:
        """Find a random problem that neither user has attempted."""
        # Get submissions for both users
        user1_submissions = self._get_user_submissions(self.username1)
        user2_submissions = self._get_user_submissions(self.username2)
        
        # Get all problems with the specified rating
        problems = self._get_problems_by_rating()
        
        # Filter out problems that either user has attempted
        unsolved_problems = []
        for problem in problems:
            problem_id = f"{problem['contestId']}{problem['index']}"
            if problem_id not in user1_submissions and problem_id not in user2_submissions:
                unsolved_problems.append(problem)
                
        if not unsolved_problems:
            return None
            
        # Select a random problem
        return random.choice(unsolved_problems)
        
    def _get_new_submissions(self, username: str) -> list:
        """Get new submissions for a user since the last check."""
        url = f"{self.base_url}/user.status"
        params = {
            "handle": username,
            "count": 1000  # Increased from 100 to 1000
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                return []
                
            new_submissions = []
            for submission in data["result"]:
                if submission["id"] > self.last_submission_ids[username]:
                    new_submissions.append(submission)
                else:
                    break
                    
            if new_submissions:
                self.last_submission_ids[username] = new_submissions[0]["id"]
                print(f"New submissions found for {username}: {len(new_submissions)}")
                
            return new_submissions
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching new submissions for {username}: {e}")
            return []
            
    def monitor_until_solved(self):
        """Monitor submissions until someone solves the target problem."""
        if not self.target_problem:
            print("No problem selected!")
            return
            
        problem_id = f"{self.target_problem['contestId']}{self.target_problem['index']}"
        print(f"\nTarget problem: {problem_id} - {self.target_problem['name']}")
        print(f"Rating: {self.rating}")
        print(f"URL: https://codeforces.com/problemset/problem/{self.target_problem['contestId']}/{self.target_problem['index']}")
        print("\nMonitoring submissions... (Press Ctrl+C to stop)")
        
        # Record start time
        self.start_time = datetime.now()
        
        try:
            while True:
                # Check for new submissions from both users
                for username in [self.username1, self.username2]:
                    new_submissions = self._get_new_submissions(username)
                    
                    for submission in reversed(new_submissions):  # Process oldest first
                        problem = submission["problem"]
                        current_problem_id = f"{problem['contestId']}{problem['index']}"
                        
                        print(f"Checking submission {submission['id']} for {username}: {current_problem_id} - {submission['verdict']}")
                        
                        if current_problem_id == problem_id and submission["verdict"] == "OK":
                            timestamp = datetime.fromtimestamp(submission["creationTimeSeconds"])
                            time_taken = datetime.now() - self.start_time
                            minutes = int(time_taken.total_seconds() // 60)
                            seconds = int(time_taken.total_seconds() % 60)
                            
                            print(f"\n{username} solved the problem!")
                            print(f"Time: {timestamp}")
                            print(f"Time taken: {minutes} minutes and {seconds} seconds")
                            return
                            
                time.sleep(5)  # Wait 5 seconds before checking again
                
        except KeyboardInterrupt:
            print("\nStopping submission monitor...")

def main():
    # Get input from user
    username1 = input("Enter first username: ")
    username2 = input("Enter second username: ")
    rating = int(input("Enter problem rating: "))
    
    # Create duel instance
    duel = CFDuel(username1, username2, rating)
    
    # Find a random problem
    print("\nFinding a random problem...")
    duel.target_problem = duel.find_random_problem()
    
    if not duel.target_problem:
        print(f"No unsolved problems found with rating {rating}")
        return
        
    # Monitor submissions until someone solves it
    duel.monitor_until_solved()

if __name__ == "__main__":
    main() 