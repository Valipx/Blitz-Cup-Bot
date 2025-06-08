import utils.session
from flask import Flask, render_template, request, jsonify
import requests
import random
from datetime import datetime
import threading
import time
from typing import Dict, Set, Optional, List
import uuid

app = Flask(__name__)

# Store active duels
active_duels = {}

class CFDuel:
    def __init__(self, username1: str, username2: str, rating: int):
        self.base_url = "https://codeforces.com/api"
        self.username1 = username1
        self.username2 = username2
        self.rating = rating
        self.target_problem = None
        self.start_time = None
        self.end_time = None
        self.status = "finding_problem"
        self.winner = None
        self.time_taken = None
        self.should_stop = False
        
    def _get_user_submissions(self, username: str) -> Set[str]:
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
        url = f"{self.base_url}/problemset.problems"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                raise Exception(f"API Error: {data['comment']}")
                
            problems = []
            for problem in data["result"]["problems"]:
                if problem.get("rating") == self.rating and problem.get("contestId", 0) > 1200:
                    problems.append(problem)
                    
            return problems
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching problems: {e}")
            return []
            
    def find_random_problem(self) -> Optional[Dict]:
        user1_submissions = self._get_user_submissions(self.username1)
        user2_submissions = self._get_user_submissions(self.username2)
        
        problems = self._get_problems_by_rating()
        
        unsolved_problems = []
        for problem in problems:
            problem_id = f"{problem['contestId']}{problem['index']}"
            if problem_id not in user1_submissions and problem_id not in user2_submissions:
                unsolved_problems.append(problem)
                
        if not unsolved_problems:
            return None
            
        return random.choice(unsolved_problems)
        
    def _check_submission(self, username: str) -> bool:
        url = f"{self.base_url}/user.status"
        params = {
            "handle": username,
            "count": 1000
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                return False
                
            problem_id = f"{self.target_problem['contestId']}{self.target_problem['index']}"
            
            for submission in data["result"]:
                problem = submission["problem"]
                current_problem_id = f"{problem['contestId']}{problem['index']}"
                
                if current_problem_id == problem_id and submission["verdict"] == "OK":
                    return True
                    
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Error checking submission for {username}: {e}")
            return False
            
    def monitor_until_solved(self):
        if not self.target_problem:
            self.status = "error"
            return
            
        self.status = "monitoring"
        self.start_time = datetime.now()
        
        while not self.should_stop:
            for username in [self.username1, self.username2]:
                if self._check_submission(username):
                    self.end_time = datetime.now()
                    time_taken = self.end_time - self.start_time
                    minutes = int(time_taken.total_seconds() // 60)
                    seconds = int(time_taken.total_seconds() % 60)
                    
                    self.winner = username
                    self.time_taken = f"{minutes} minutes and {seconds} seconds"
                    self.status = "completed"
                    return
                    
            time.sleep(5)
            
        self.status = "ended"
        
    def end_duel(self):
        self.should_stop = True
        self.status = "ended"

def start_duel(username1: str, username2: str, rating: int) -> str:
    duel_id = f"{username1}_{username2}_{int(time.time())}"
    duel = CFDuel(username1, username2, rating)
    active_duels[duel_id] = duel
    
    # Start monitoring in a separate thread
    def run_duel():
        duel.target_problem = duel.find_random_problem()
        if duel.target_problem:
            duel.monitor_until_solved()
        else:
            duel.status = "error"
    
    thread = threading.Thread(target=run_duel)
    thread.start()
    
    return duel_id

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_duel', methods=['POST'])
def start_duel_route():
    data = request.get_json()
    username1 = data.get('username1')
    username2 = data.get('username2')
    rating = int(data.get('rating'))
    
    if not all([username1, username2, rating]):
        return jsonify({'error': 'Missing required parameters'}), 400
        
    duel_id = start_duel(username1, username2, rating)
    return jsonify({'duel_id': duel_id})

@app.route('/duel_status/<duel_id>')
def duel_status(duel_id):
    if duel_id not in active_duels:
        return jsonify({'error': 'Duel not found'}), 404
        
    duel = active_duels[duel_id]
    response = {
        'status': duel.status,
        'username1': duel.username1,
        'username2': duel.username2,
        'rating': duel.rating,
        'start_time': duel.start_time.strftime('%Y-%m-%d %H:%M:%S') if duel.start_time else None,
        'end_time': duel.end_time.strftime('%Y-%m-%d %H:%M:%S') if duel.end_time else None,
        'time_taken': duel.time_taken
    }
    
    if duel.target_problem:
        response['problem'] = {
            'id': f"{duel.target_problem['contestId']}{duel.target_problem['index']}",
            'name': duel.target_problem['name'],
            'url': f"https://codeforces.com/problemset/problem/{duel.target_problem['contestId']}/{duel.target_problem['index']}"
        }
        
    if duel.winner:
        response['winner'] = duel.winner

    if duel.status == 'error':
        response['error'] = 'An error occurred'

    return jsonify(response)

@app.route('/end_duel/<duel_id>', methods=['POST'])
def end_duel(duel_id):
    if duel_id not in active_duels:
        return jsonify({'error': 'Duel not found'}), 404
        
    duel = active_duels[duel_id]
    duel.end_duel()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True) 