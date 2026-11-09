from typing import List, Dict, Any, Optional
from datetime import datetime


class MockGraphAdapter:
    """Mock implementation of GraphAdapter for testing"""
    
    def __init__(self):
        # Forward paths from source accounts
        self.mock_forward_paths = {
            "A001": [
                {
                    "path": ["A001", "A002", "A003"],
                    "amount": 30000,
                    "tainted_amount": 27000,
                    "hops": 2,
                    "transactions": ["T1001", "T1002"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00"]
                },
                {
                    "path": ["A001", "A002", "A004"],
                    "amount": 20000,
                    "tainted_amount": 15000,
                    "hops": 2,
                    "transactions": ["T1001", "T1003"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:30:00"]
                },
                {
                    "path": ["A001", "A002", "A003", "A005"],
                    "amount": 15000,
                    "tainted_amount": 13500,
                    "hops": 3,
                    "transactions": ["T1001", "T1002", "T1004"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00", "2026-08-17T11:00:00"]
                },
                {
                    "path": ["A001", "A002", "A003", "A006"],
                    "amount": 15000,
                    "tainted_amount": 13500,
                    "hops": 3,
                    "transactions": ["T1001", "T1002", "T1005"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00", "2026-08-17T11:15:00"]
                },
                {
                    "path": ["A001", "A002", "A004", "A007"],
                    "amount": 20000,
                    "tainted_amount": 15000,
                    "hops": 3,
                    "transactions": ["T1001", "T1003", "T1006"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:30:00", "2026-08-17T11:30:00"]
                }
            ],
            "A002": [
                {
                    "path": ["A002", "A003", "A005"],
                    "amount": 15000,
                    "tainted_amount": 13500,
                    "hops": 2,
                    "transactions": ["T1002", "T1004"],
                    "timestamps": ["2026-08-17T10:15:00", "2026-08-17T11:00:00"]
                },
                {
                    "path": ["A002", "A003", "A006"],
                    "amount": 15000,
                    "tainted_amount": 13500,
                    "hops": 2,
                    "transactions": ["T1002", "T1005"],
                    "timestamps": ["2026-08-17T10:15:00", "2026-08-17T11:15:00"]
                }
            ]
        }
        
        # Backward paths to target accounts
        self.mock_backward_paths = {
            "A005": [
                {
                    "path": ["A001", "A002", "A003", "A005"],
                    "amount": 15000,
                    "tainted_amount": 13500,
                    "hops": 3,
                    "transactions": ["T1001", "T1002", "T1004"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00", "2026-08-17T11:00:00"]
                }
            ],
            "A006": [
                {
                    "path": ["A001", "A002", "A003", "A006"],
                    "amount": 15000,
                    "tainted_amount": 13500,
                    "hops": 3,
                    "transactions": ["T1001", "T1002", "T1005"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00", "2026-08-17T11:15:00"]
                }
            ],
            "A007": [
                {
                    "path": ["A001", "A002", "A004", "A007"],
                    "amount": 20000,
                    "tainted_amount": 15000,
                    "hops": 3,
                    "transactions": ["T1001", "T1003", "T1006"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:30:00", "2026-08-17T11:30:00"]
                }
            ],
            "A008": [
                {
                    "path": ["A001", "A002", "A003", "A005", "A008"],
                    "amount": 10000,
                    "tainted_amount": 9000,
                    "hops": 4,
                    "transactions": ["T1001", "T1002", "T1004", "T1007"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00", 
                                  "2026-08-17T11:00:00", "2026-08-17T12:00:00"]
                }
            ],
            "A009": [
                {
                    "path": ["A001", "A002", "A003", "A006", "A009"],
                    "amount": 8000,
                    "tainted_amount": 7200,
                    "hops": 4,
                    "transactions": ["T1001", "T1002", "T1005", "T1008"],
                    "timestamps": ["2026-08-17T10:00:00", "2026-08-17T10:15:00",
                                  "2026-08-17T11:15:00", "2026-08-17T12:15:00"]
                }
            ]
        }
        
        # Adjacency list for graph traversal
        self.mock_adjacency = {
            "A001": {"outgoing": ["A002"], "incoming": []},
            "A002": {"outgoing": ["A003", "A004"], "incoming": ["A001"]},
            "A003": {"outgoing": ["A005", "A006"], "incoming": ["A002"]},
            "A004": {"outgoing": ["A007"], "incoming": ["A002"]},
            "A005": {"outgoing": ["A008"], "incoming": ["A003"]},
            "A006": {"outgoing": ["A009"], "incoming": ["A003"]},
            "A007": {"outgoing": [], "incoming": ["A004"]},
            "A008": {"outgoing": [], "incoming": ["A005"]},
            "A009": {"outgoing": [], "incoming": ["A006"]},
            "A010": {"outgoing": [], "incoming": ["A001"]}
        }
    
    def trace_forward(self, source: str, max_hops: int, 
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Trace forward from source account
        """
        paths = self.mock_forward_paths.get(source, [])
        
        # Filter by max_hops
        filtered_paths = [p for p in paths if p["hops"] <= max_hops]
        
        # Filter by time if provided
        if start_time or end_time:
            time_filtered = []
            for path in filtered_paths:
                if start_time:
                    path_start = datetime.fromisoformat(path["timestamps"][0])
                    if path_start < start_time:
                        continue
                if end_time:
                    path_end = datetime.fromisoformat(path["timestamps"][-1])
                    if path_end > end_time:
                        continue
                time_filtered.append(path)
            return time_filtered
        
        return filtered_paths
    
    def trace_backward(self, target: str, max_hops: int,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Trace backward from target account
        """
        paths = self.mock_backward_paths.get(target, [])
        
        # Filter by max_hops
        filtered_paths = [p for p in paths if p["hops"] <= max_hops]
        
        # Filter by time if provided
        if start_time or end_time:
            time_filtered = []
            for path in filtered_paths:
                if start_time:
                    path_start = datetime.fromisoformat(path["timestamps"][0])
                    if path_start < start_time:
                        continue
                if end_time:
                    path_end = datetime.fromisoformat(path["timestamps"][-1])
                    if path_end > end_time:
                        continue
                time_filtered.append(path)
            return time_filtered
        
        return filtered_paths
    
    def get_adjacent_accounts(self, account_id: str, direction: str = "both") -> List[str]:
        """
        Get accounts adjacent to the given account
        """
        adj = self.mock_adjacency.get(account_id, {"outgoing": [], "incoming": []})
        
        if direction == "forward":
            return adj["outgoing"]
        elif direction == "backward":
            return adj["incoming"]
        else:  # both
            return adj["outgoing"] + adj["incoming"]
    
    def get_path_between_accounts(self, source: str, target: str, 
                                  max_hops: int) -> Optional[List[str]]:
        """
        Find a path between two accounts using BFS
        """
        from collections import deque
        
        visited = set()
        queue = deque([(source, [source])])
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) - 1 > max_hops:
                continue
                
            if current == target:
                return path
            
            if current not in visited:
                visited.add(current)
                neighbors = self.get_adjacent_accounts(current, "forward")
                
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, path + [neighbor]))
        
        return None
