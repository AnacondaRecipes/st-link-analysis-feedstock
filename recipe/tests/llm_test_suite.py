import pytest
import json
import sys
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Mock st-link-analysis components if not installed
try:
    from st_link_analysis import NodeStyle, EdgeStyle
except ImportError:
    # Create mock classes for testing
    class NodeStyle:
        def __init__(self, label: str, color: str, caption: str, icon: str):
            self.label = label
            self.color = color
            self.caption = caption
            self.icon = icon
    
    class EdgeStyle:
        def __init__(self, label: str, caption: str = "label", color: str = "#999", directed: bool = False):
            self.label = label
            self.caption = caption
            self.color = color
            self.directed = directed


class NetworkDataValidator:
    """Standalone network data validator for st-link-analysis"""
    
    @staticmethod
    def validate_elements(elements: Dict[str, List[Dict]]) -> List[str]:
        """Validate network elements structure"""
        errors = []
        
        if not isinstance(elements, dict):
            errors.append("Elements must be a dictionary")
            return errors
        
        # Check required keys
        if "nodes" not in elements:
            errors.append("Missing 'nodes' key in elements")
        if "edges" not in elements:
            errors.append("Missing 'edges' key in elements")
        
        if errors:
            return errors
        
        # Validate nodes
        node_ids = set()
        for i, node in enumerate(elements.get("nodes", [])):
            node_errors = NetworkDataValidator._validate_node(node, i)
            errors.extend(node_errors)
            
            if "data" in node and "id" in node["data"]:
                node_id = node["data"]["id"]
                if node_id in node_ids:
                    errors.append(f"Duplicate node ID: {node_id}")
                node_ids.add(node_id)
        
        # Validate edges
        for i, edge in enumerate(elements.get("edges", [])):
            edge_errors = NetworkDataValidator._validate_edge(edge, i, node_ids)
            errors.extend(edge_errors)
        
        return errors
    
    @staticmethod
    def _validate_node(node: Dict, index: int) -> List[str]:
        """Validate individual node structure"""
        errors = []
        
        if not isinstance(node, dict):
            errors.append(f"Node {index} must be a dictionary")
            return errors
        
        if "data" not in node:
            errors.append(f"Node {index} missing 'data' key")
            return errors
        
        data = node["data"]
        if not isinstance(data, dict):
            errors.append(f"Node {index} 'data' must be a dictionary")
            return errors
        
        if "id" not in data:
            errors.append(f"Node {index} missing 'id' in data")
        
        if "label" not in data:
            errors.append(f"Node {index} missing 'label' in data")
        
        return errors
    
    @staticmethod
    def _validate_edge(edge: Dict, index: int, valid_node_ids: set) -> List[str]:
        """Validate individual edge structure"""
        errors = []
        
        if not isinstance(edge, dict):
            errors.append(f"Edge {index} must be a dictionary")
            return errors
        
        if "data" not in edge:
            errors.append(f"Edge {index} missing 'data' key")
            return errors
        
        data = edge["data"]
        if not isinstance(data, dict):
            errors.append(f"Edge {index} 'data' must be a dictionary")
            return errors
        
        # Check required fields
        required_fields = ["id", "source", "target"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Edge {index} missing '{field}' in data")
        
        # Validate references to nodes
        if "source" in data and data["source"] not in valid_node_ids:
            errors.append(f"Edge {index} source {data['source']} not found in nodes")
        
        if "target" in data and data["target"] not in valid_node_ids:
            errors.append(f"Edge {index} target {data['target']} not found in nodes")
        
        return errors


class NetworkBuilder:
    """Helper class to build test networks"""
    
    def __init__(self):
        self.elements = {"nodes": [], "edges": []}
        self.next_id = 1
    
    def add_node(self, label: str, name: str = None, **kwargs) -> int:
        """Add a node and return its ID"""
        node_id = self.next_id
        self.next_id += 1
        
        node_data = {
            "id": node_id,
            "label": label,
            "name": name or f"Node{node_id}",
            **kwargs
        }
        
        self.elements["nodes"].append({"data": node_data})
        return node_id
    
    def add_edge(self, source: int, target: int, label: str = "CONNECTS", **kwargs) -> int:
        """Add an edge and return its ID"""
        edge_id = self.next_id
        self.next_id += 1
        
        edge_data = {
            "id": edge_id,
            "source": source,
            "target": target,
            "label": label,
            **kwargs
        }
        
        self.elements["edges"].append({"data": edge_data})
        return edge_id
    
    def get_elements(self) -> Dict[str, List[Dict]]:
        """Get the complete network elements"""
        return self.elements.copy()


def mock_st_link_analysis(elements, layout=None, node_styles=None, edge_styles=None, 
                         height=400, node_actions=True, key=None):
    """Mock st_link_analysis function for testing"""
    # Validate inputs
    validator = NetworkDataValidator()
    errors = validator.validate_elements(elements)
    
    if errors:
        raise ValueError(f"Invalid network data: {errors}")
    
    # Simulate component behavior
    result = {
        "nodes_count": len(elements["nodes"]),
        "edges_count": len(elements["edges"]),
        "layout": layout or {"name": "grid"},
        "height": height,
        "selected_nodes": [],
        "event": None
    }
    
    return result


class TestStLinkAnalysisHeadless:
    """Headless tests for st-link-analysis functionality"""
    
    def test_node_style_creation(self):
        """Test NodeStyle object creation"""
        style = NodeStyle("PERSON", "#FF0000", "name", "person")
        
        assert style.label == "PERSON"
        assert style.color == "#FF0000"
        assert style.caption == "name"
        assert style.icon == "person"
    
    def test_edge_style_creation(self):
        """Test EdgeStyle object creation"""
        style = EdgeStyle("CONNECTS", caption="label", color="#0000FF", directed=True)
        
        assert style.label == "CONNECTS"
        assert style.color == "#0000FF"
        assert style.caption == "label"
        assert style.directed == True
    
    def test_network_data_validation_valid(self):
        """Test validation with valid network data"""
        elements = {
            "nodes": [
                {"data": {"id": 1, "label": "PERSON", "name": "Alice"}},
                {"data": {"id": 2, "label": "PERSON", "name": "Bob"}}
            ],
            "edges": [
                {"data": {"id": 3, "source": 1, "target": 2, "label": "KNOWS"}}
            ]
        }
        
        validator = NetworkDataValidator()
        errors = validator.validate_elements(elements)
        
        assert len(errors) == 0, f"Valid data should not have errors: {errors}"
    
    def test_network_data_validation_invalid_structure(self):
        """Test validation with invalid structure"""
        invalid_elements = [
            # Missing nodes/edges keys
            {},
            # Invalid node structure
            {
                "nodes": [{"invalid": "structure"}],
                "edges": []
            },
            # Missing node data
            {
                "nodes": [{}],
                "edges": []
            },
            # Invalid edge references
            {
                "nodes": [{"data": {"id": 1, "label": "TEST"}}],
                "edges": [{"data": {"id": 2, "source": 1, "target": 99, "label": "INVALID"}}]
            }
        ]
        
        validator = NetworkDataValidator()
        
        for i, elements in enumerate(invalid_elements):
            errors = validator.validate_elements(elements)
            assert len(errors) > 0, f"Invalid elements {i} should have errors"
    
    def test_duplicate_node_ids(self):
        """Test detection of duplicate node IDs"""
        elements = {
            "nodes": [
                {"data": {"id": 1, "label": "TEST", "name": "Node1"}},
                {"data": {"id": 1, "label": "TEST", "name": "Node2"}}  # Duplicate ID
            ],
            "edges": []
        }
        
        validator = NetworkDataValidator()
        errors = validator.validate_elements(elements)
        
        assert len(errors) > 0
        assert any("Duplicate node ID: 1" in error for error in errors)
    
    def test_network_builder(self):
        """Test NetworkBuilder helper class"""
        builder = NetworkBuilder()
        
        # Add nodes
        node1 = builder.add_node("PERSON", "Alice", age=30)
        node2 = builder.add_node("PERSON", "Bob", age=25)
        
        # Add edge
        edge1 = builder.add_edge(node1, node2, "KNOWS", strength=0.8)
        
        elements = builder.get_elements()
        
        # Validate structure
        assert len(elements["nodes"]) == 2
        assert len(elements["edges"]) == 1
        
        # Check node data
        assert elements["nodes"][0]["data"]["name"] == "Alice"
        assert elements["nodes"][0]["data"]["age"] == 30
        assert elements["nodes"][1]["data"]["name"] == "Bob"
        
        # Check edge data
        assert elements["edges"][0]["data"]["source"] == node1
        assert elements["edges"][0]["data"]["target"] == node2
        assert elements["edges"][0]["data"]["strength"] == 0.8
    
    @patch('builtins.print')  # Mock print to capture output
    def test_mock_component_execution(self, mock_print):
        """Test mock component execution"""
        # Create test data
        builder = NetworkBuilder()
        node1 = builder.add_node("SERVER", "WebServer")
        node2 = builder.add_node("DATABASE", "MainDB")
        builder.add_edge(node1, node2, "CONNECTS")
        
        elements = builder.get_elements()
        
        # Test component call
        result = mock_st_link_analysis(
            elements=elements,
            layout={"name": "cola"},
            height=500,
            key="test_graph"
        )
        
        # Validate result
        assert result["nodes_count"] == 2
        assert result["edges_count"] == 1
        assert result["layout"]["name"] == "cola"
        assert result["height"] == 500
        assert isinstance(result["selected_nodes"], list)
    
    def test_component_with_invalid_data(self):
        """Test component behavior with invalid data"""
        invalid_elements = {
            "nodes": [{"data": {"id": 1, "label": "TEST"}}],
            "edges": [{"data": {"id": 2, "source": 1, "target": 99, "label": "INVALID"}}]
        }
        
        with pytest.raises(ValueError) as exc_info:
            mock_st_link_analysis(elements=invalid_elements)
        
        assert "Invalid network data" in str(exc_info.value)
    
    def test_large_network_performance(self):
        """Test with larger network to check performance"""
        builder = NetworkBuilder()
        
        # Create 100 nodes
        nodes = []
        for i in range(100):
            node_id = builder.add_node("NODE", f"Node{i}", index=i)
            nodes.append(node_id)
        
        # Create 200 random edges
        import random
        random.seed(42)  # For reproducible tests
        
        for i in range(200):
            source = random.choice(nodes)
            target = random.choice(nodes)
            if source != target:  # Avoid self-loops
                builder.add_edge(source, target, "CONNECTS", weight=random.random())
        
        elements = builder.get_elements()
        
        # Validate large network
        validator = NetworkDataValidator()
        errors = validator.validate_elements(elements)
        
        assert len(errors) == 0, f"Large network should be valid: {errors}"
        assert len(elements["nodes"]) == 100
        assert len(elements["edges"]) <= 200  # Some edges might be duplicates
    
    def test_network_statistics(self):
        """Test basic network statistics calculation"""
        builder = NetworkBuilder()
        
        # Create a simple network
        n1 = builder.add_node("PERSON", "Alice")
        n2 = builder.add_node("PERSON", "Bob") 
        n3 = builder.add_node("PERSON", "Carol")
        
        builder.add_edge(n1, n2, "KNOWS")
        builder.add_edge(n2, n3, "KNOWS")
        builder.add_edge(n1, n3, "KNOWS")
        
        elements = builder.get_elements()
        
        # Calculate basic statistics
        node_count = len(elements["nodes"])
        edge_count = len(elements["edges"])
        
        # Calculate node degrees
        degrees = {}
        for edge in elements["edges"]:
            source = edge["data"]["source"]
            target = edge["data"]["target"]
            degrees[source] = degrees.get(source, 0) + 1
            degrees[target] = degrees.get(target, 0) + 1
        
        avg_degree = sum(degrees.values()) / len(degrees)
        
        assert node_count == 3
        assert edge_count == 3
        assert avg_degree == 2.0  # Each node connected to 2 others


def main():
    """Run tests manually if needed"""
    print("Running st-link-analysis headless tests...")
    
    # Create test instance
    test_instance = TestStLinkAnalysisHeadless()
    
    # Run all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"Running {method_name}...", end=" ")
            method = getattr(test_instance, method_name)
            method()
            print("PASSED")
            passed += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)