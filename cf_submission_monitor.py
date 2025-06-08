import requests
import time
from typing import Dict, Set, Optional
from datetime import datetime

class CFSubmissionMonitor:
    def __init__(self, username1: str, username2: str):
        self.base_url = "https://codeforces.com/api"
        self.username1 = username1
        self.username2 = username2
        self.last_submission_ids = {
            username1: self._get_latest_submission_id(username1),
            username2: self._get_latest_submission_id(username2)
        }
        self.solved_problems = {
            username1: self._get_solved_problems(username1),
            username2: self._get_solved_problems(username2)
        }
        
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
            
    def _get_solved_problems(self, username: str) -> Set[str]:
        """Get all problems that a user has solved."""
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
                
            solved_problems = set()
            for submission in data["result"]:
                if submission["verdict"] == "OK":
                    problem = submission["problem"]
                    problem_id = f"{problem['contestId']}{problem['index']}"
                    solved_problems.add(problem_id)
                    
            return solved_problems
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching solved problems for {username}: {e}")
            return set()
            
    def _get_new_submissions(self, username: str) -> list:
        """Get new submissions for a user since the last check."""
        url = f"{self.base_url}/user.status"
        params = {
            "handle": username,
            "count": 100
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
                
            return new_submissions
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching new submissions for {username}: {e}")
            return []
            
    def monitor_submissions(self):
        """Monitor submissions for both users in real-time."""
        print(f"Starting to monitor submissions for {self.username1} and {self.username2}")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Check for new submissions from both users
                for username in [self.username1, self.username2]:
                    new_submissions = self._get_new_submissions(username)
                    
                    for submission in reversed(new_submissions):  # Process oldest first
                        problem = submission["problem"]
                        problem_id = f"{problem['contestId']}{problem['index']}"
                        
                        # Only process submissions for problems with contest ID > 1200
                        if problem["contestId"] <= 1200:
                            continue
                            
                        if submission["verdict"] == "OK":
                            # Check if this is the first accepted submission for this problem
                            if problem_id not in self.solved_problems[self.username1] and \
                               problem_id not in self.solved_problems[self.username2]:
                                timestamp = datetime.fromtimestamp(submission["creationTimeSeconds"])
                                print(f"\n{username} solved problem {problem_id} first!")
                                print(f"Problem: {problem['name']}")
                                print(f"Time: {timestamp}")
                                print(f"Rating: {problem.get('rating', 'Unknown')}")
                                
                            # Add to solved problems
                            self.solved_problems[username].add(problem_id)
                            
                time.sleep(5)  # Wait 5 seconds before checking again
                
        except KeyboardInterrupt:
            print("\nStopping submission monitor...")

def main():
    username1 = input("Enter first username: ")
    username2 = input("Enter second username: ")
    
    monitor = CFSubmissionMonitor(username1, username2)
    monitor.monitor_submissions()

if __name__ == "__main__":
    main() 