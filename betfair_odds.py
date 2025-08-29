"""
Betfair Exchange API integration for Super Bowl winner odds
This module fetches current betting odds for Super Bowl winners from Betfair Exchange
"""

import requests
import json
import pandas as pd
from datetime import datetime
import os
from typing import Dict, List, Optional

class BetfairAPI:
    """
    Betfair Exchange API client for fetching Super Bowl odds
    """
    
    def __init__(self):
        self.base_url = "https://api.betfair.com/exchange/betting/rest/v1.0/"
        self.session_token = None
        self.app_key = os.getenv('BETFAIR_APP_KEY')  # Set in environment variables
        self.username = os.getenv('BETFAIR_USERNAME')
        self.password = os.getenv('BETFAIR_PASSWORD')
        
        if not all([self.app_key, self.username, self.password]):
            print("Warning: Betfair credentials not found in environment variables")
            print("Set BETFAIR_APP_KEY, BETFAIR_USERNAME, and BETFAIR_PASSWORD")
    
    def login(self) -> bool:
        """
        Authenticate with Betfair API
        Returns True if successful, False otherwise
        """
        login_url = "https://identitysso.betfair.com/api/certlogin"
        
        headers = {
            'X-Application': self.app_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = requests.post(login_url, headers=headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            if result['status'] == 'SUCCESS':
                self.session_token = result['token']
                print("Successfully logged in to Betfair")
                return True
            else:
                print(f"Login failed: {result}")
                return False
                
        except requests.RequestException as e:
            print(f"Login error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'X-Application': self.app_key,
            'X-Authentication': self.session_token,
            'Content-Type': 'application/json'
        }
    
    def find_superbowl_market(self) -> Optional[str]:
        """
        Find the Super Bowl winner market ID
        Returns market ID if found, None otherwise
        """
        if not self.session_token:
            if not self.login():
                return None
        
        # Search for American Football events
        url = f"{self.base_url}listEventTypes/"
        
        try:
            response = requests.post(
                url,
                headers=self.get_headers(),
                json={"filter": {}}
            )
            response.raise_for_status()
            event_types = response.json()
            
            # Find American Football event type
            american_football_id = None
            for event_type in event_types:
                if 'american football' in event_type['eventType']['name'].lower():
                    american_football_id = event_type['eventType']['id']
                    break
            
            if not american_football_id:
                print("American Football not found in event types")
                return None
            
            # Get competitions for American Football
            url = f"{self.base_url}listCompetitions/"
            response = requests.post(
                url,
                headers=self.get_headers(),
                json={"filter": {"eventTypeIds": [american_football_id]}}
            )
            response.raise_for_status()
            competitions = response.json()
            
            # Find NFL competition
            nfl_competition_id = None
            for comp in competitions:
                if 'nfl' in comp['competition']['name'].lower():
                    nfl_competition_id = comp['competition']['id']
                    break
            
            if not nfl_competition_id:
                print("NFL competition not found")
                return None
            
            # Get market catalogue for Super Bowl
            url = f"{self.base_url}listMarketCatalogue/"
            response = requests.post(
                url,
                headers=self.get_headers(),
                json={
                    "filter": {
                        "eventTypeIds": [american_football_id],
                        "competitionIds": [nfl_competition_id],
                        "textQuery": "Super Bowl"
                    },
                    "marketProjection": ["COMPETITION", "EVENT", "EVENT_TYPE", "MARKET_DESCRIPTION"],
                    "maxResults": 100
                }
            )
            response.raise_for_status()
            markets = response.json()
            
            # Find the Super Bowl winner market
            for market in markets:
                market_name = market.get('marketName', '').lower()
                if 'winner' in market_name and 'super bowl' in market_name:
                    return market['marketId']
            
            print("Super Bowl winner market not found")
            return None
            
        except requests.RequestException as e:
            print(f"Error finding Super Bowl market: {e}")
            return None
    
    def get_superbowl_odds(self) -> Optional[pd.DataFrame]:
        """
        Fetch current Super Bowl winner odds
        Returns DataFrame with team names and odds
        """
        market_id = self.find_superbowl_market()
        if not market_id:
            return None
        
        # Get market book (current odds)
        url = f"{self.base_url}listMarketBook/"
        
        try:
            response = requests.post(
                url,
                headers=self.get_headers(),
                json={
                    "marketIds": [market_id],
                    "priceProjection": {
                        "priceData": ["EX_BEST_OFFERS"]
                    }
                }
            )
            response.raise_for_status()
            market_book = response.json()
            
            if not market_book:
                print("No market book data received")
                return None
            
            # Get runner details (team names)
            url = f"{self.base_url}listMarketCatalogue/"
            response = requests.post(
                url,
                headers=self.get_headers(),
                json={
                    "filter": {"marketIds": [market_id]},
                    "marketProjection": ["RUNNER_DESCRIPTION"]
                }
            )
            response.raise_for_status()
            market_catalogue = response.json()
            
            # Process the data
            odds_data = []
            market_data = market_book[0]
            runner_descriptions = {runner['selectionId']: runner['runnerName'] 
                                 for runner in market_catalogue[0]['runners']}
            
            for runner in market_data['runners']:
                selection_id = runner['selectionId']
                team_name = runner_descriptions.get(selection_id, f"Unknown ({selection_id})")
                
                # Get best back price (odds)
                best_back_price = None
                if runner.get('ex', {}).get('availableToBack'):
                    best_back_price = runner['ex']['availableToBack'][0]['price']
                
                odds_data.append({
                    'team': team_name,
                    'odds': best_back_price,
                    'selection_id': selection_id,
                    'status': runner['status']
                })
            
            df = pd.DataFrame(odds_data)
            df = df[df['status'] == 'ACTIVE']  # Only active runners
            df = df.sort_values('odds', ascending=True)  # Sort by best odds first
            
            return df[['team', 'odds']]
            
        except requests.RequestException as e:
            print(f"Error fetching odds: {e}")
            return None

def get_mock_superbowl_odds() -> pd.DataFrame:
    """
    Generate mock Super Bowl odds for testing when Betfair API is not available
    """
    teams_odds = [
        ("Kansas City Chiefs", 5.5),
        ("Buffalo Bills", 7.0),
        ("San Francisco 49ers", 8.0),
        ("Philadelphia Eagles", 9.0),
        ("Baltimore Ravens", 10.0),
        ("Detroit Lions", 12.0),
        ("Green Bay Packers", 15.0),
        ("Miami Dolphins", 18.0),
        ("Houston Texans", 20.0),
        ("Dallas Cowboys", 22.0),
        ("Los Angeles Chargers", 25.0),
        ("Cincinnati Bengals", 28.0),
        ("Pittsburgh Steelers", 30.0),
        ("Minnesota Vikings", 35.0),
        ("Atlanta Falcons", 40.0),
        ("Los Angeles Rams", 45.0),
        ("Seattle Seahawks", 50.0),
        ("Tampa Bay Buccaneers", 55.0),
        ("Indianapolis Colts", 60.0),
        ("New York Jets", 65.0),
        ("Cleveland Browns", 70.0),
        ("Jacksonville Jaguars", 75.0),
        ("Denver Broncos", 80.0),
        ("Washington Commanders", 85.0),
        ("Arizona Cardinals", 90.0),
        ("Tennessee Titans", 95.0),
        ("New Orleans Saints", 100.0),
        ("Las Vegas Raiders", 110.0),
        ("Chicago Bears", 120.0),
        ("Carolina Panthers", 130.0),
        ("New York Giants", 140.0),
        ("New England Patriots", 150.0)
    ]
    
    df = pd.DataFrame(teams_odds, columns=['team', 'odds'])
    df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return df

def save_odds_to_csv(df: pd.DataFrame, filename: str = "betfair_superbowl_odds.csv"):
    """Save odds data to CSV file"""
    df.to_csv(filename, index=False)
    print(f"Odds saved to {filename}")

def main():
    """Main function to fetch and save Super Bowl odds"""
    print("Fetching Super Bowl winner odds from Betfair Exchange...")
    
    # Try to use real Betfair API
    betfair = BetfairAPI()
    
    if betfair.app_key and betfair.username and betfair.password:
        odds_df = betfair.get_superbowl_odds()
        
        if odds_df is not None:
            print("Successfully fetched real odds from Betfair!")
            odds_df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_odds_to_csv(odds_df)
            print(f"Found odds for {len(odds_df)} teams")
            print("\nTop 10 favorites:")
            print(odds_df.head(10).to_string(index=False))
            return
    
    # Fall back to mock data
    print("Using mock odds data (Betfair API not configured)")
    mock_odds = get_mock_superbowl_odds()
    save_odds_to_csv(mock_odds)
    print(f"Generated mock odds for {len(mock_odds)} teams")
    print("\nTop 10 favorites:")
    print(mock_odds.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
