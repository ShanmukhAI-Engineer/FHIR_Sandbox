"""
Dependency Graph - Manage resource dependencies and execution order
"""

from typing import List, Dict, Set
from collections import defaultdict
from config.resources import RESOURCES

class DependencyGraph:
    """
    Manages resource dependencies to determine correct generation order.
    """
    
    def __init__(self, output_resources: List[str]):
        self.resources = output_resources
        self.graph = defaultdict(set)
        self._build_graph()
    
    def _build_graph(self):
        """Build the dependency graph based on config"""
        for resource in self.resources:
            config = RESOURCES.get(resource)
            if not config:
                continue
                
            relationships = config.get("relationships", [])
            for rel in relationships:
                ref_resource = rel["references"].split(".")[0]
                
                # Only add dependency if the referenced resource is also being generated
                # or if we want to enforce global order. 
                # For now, we only care about sorting the *requested* resources.
                if ref_resource in self.resources:
                    self.graph[resource].add(ref_resource)

    def get_execution_order(self) -> List[str]:
        """
        Get resources sorted by dependency order (Topological Sort).
        Returns a list where parents come before children.
        """
        visited = set()
        temp_mark = set()
        order = []
        
        def visit(node):
            if node in temp_mark:
                # Cycle detected, break it arbitrarily or warn
                return
            if node in visited:
                return
            
            temp_mark.add(node)
            
            for parent in self.graph[node]:
                visit(parent)
            
            temp_mark.remove(node)
            visited.add(node)
            order.append(node)
        
        # Sort nodes to ensure deterministic output for independent nodes
        for resource in sorted(self.resources):
            visit(resource)
            
        return order

    def get_parents(self, resource: str) -> List[str]:
        """Get list of immediate parent resources for a given resource"""
        config = RESOURCES.get(resource)
        if not config:
            return []
            
        parents = set()
        for rel in config.get("relationships", []):
            ref = rel.get("references", "").split(".")[0]
            if ref:
                parents.add(ref)
        
        return list(parents)

    def get_missing_dependencies(self, selected_resources: List[str]) -> List[str]:
        """
        Identify missing parent resources for the current selection.
        Returns a list of unique missing resources that are required by the selected ones.
        """
        missing = set()
        selected_set = set(selected_resources)
        
        for resource in selected_resources:
            parents = self.get_parents(resource)
            for parent in parents:
                if parent not in selected_set:
                    missing.add(parent)
        
        return list(missing)
