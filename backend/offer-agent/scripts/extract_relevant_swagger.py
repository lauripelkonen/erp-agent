#!/usr/bin/env python3
"""
Script to extract relevant API endpoints from the full Swagger documentation.
Creates a filtered version that only includes specified endpoints while preserving
all necessary structure for MCP server generation.
"""

import json
import re
from pathlib import Path


def load_swagger_doc(file_path):
    """Load the full swagger documentation."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_relevant_endpoints(swagger_doc, endpoint_patterns):
    """
    Extract only the relevant endpoints and their dependencies.
    
    Args:
        swagger_doc: Full swagger documentation
        endpoint_patterns: List of endpoint patterns to include
    
    Returns:
        Filtered swagger documentation
    """
    # Create a new swagger doc with the same base structure
    filtered_doc = {
        "swagger": swagger_doc["swagger"],
        "info": swagger_doc["info"],
        "host": swagger_doc["host"],
        "basePath": swagger_doc["basePath"],
        "schemes": swagger_doc["schemes"],
        "paths": {},
        "definitions": {}
    }
    
    # Copy any additional top-level properties that might be present
    for key in swagger_doc:
        if key not in filtered_doc and key != "paths" and key != "definitions":
            filtered_doc[key] = swagger_doc[key]
    
    # Track which definitions are referenced
    referenced_definitions = set()
    
    # Extract matching paths
    for path, path_obj in swagger_doc["paths"].items():
        # Clean the path for comparison (remove leading slash and basePath)
        clean_path = path.lstrip('/')
        if clean_path.startswith('api/'):
            clean_path = clean_path[4:]  # Remove 'api/' prefix
        
        # Check if this path matches any of our endpoint patterns
        path_matches = False
        for pattern in endpoint_patterns:
            if matches_endpoint_pattern(clean_path, pattern):
                path_matches = True
                break
        
        if path_matches:
            filtered_doc["paths"][path] = path_obj
            # Track referenced definitions from this path
            collect_references(path_obj, referenced_definitions)
    
    # Extract referenced definitions and their dependencies
    extract_definitions(swagger_doc, filtered_doc, referenced_definitions)
    
    return filtered_doc


def matches_endpoint_pattern(path, pattern):
    """
    Check if a path matches an endpoint pattern.
    Supports patterns like 'customers/{customer_id}' where {customer_id} matches any value.
    """
    # Convert pattern to regex
    # Replace {param} with regex pattern that matches path parameters
    regex_pattern = re.escape(pattern)
    regex_pattern = regex_pattern.replace(r'\{[^}]+\}', r'[^/]+')
    regex_pattern = f"^{regex_pattern}$"
    
    return re.match(regex_pattern, path) is not None


def collect_references(obj, referenced_definitions):
    """Recursively collect all $ref references from an object."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref" and isinstance(value, str):
                # Extract definition name from $ref
                if value.startswith("#/definitions/"):
                    def_name = value.replace("#/definitions/", "")
                    referenced_definitions.add(def_name)
            else:
                collect_references(value, referenced_definitions)
    elif isinstance(obj, list):
        for item in obj:
            collect_references(item, referenced_definitions)


def extract_definitions(source_doc, target_doc, referenced_definitions):
    """Extract definitions and their dependencies recursively."""
    if "definitions" not in source_doc:
        return
    
    # Keep adding definitions until no new ones are found
    while True:
        initial_count = len(target_doc["definitions"])
        
        for def_name in list(referenced_definitions):
            if def_name in source_doc["definitions"] and def_name not in target_doc["definitions"]:
                target_doc["definitions"][def_name] = source_doc["definitions"][def_name]
                # Collect references from this definition
                collect_references(source_doc["definitions"][def_name], referenced_definitions)
        
        # If no new definitions were added, we're done
        if len(target_doc["definitions"]) == initial_count:
            break


def save_filtered_doc(filtered_doc, output_path):
    """Save the filtered documentation to a file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_doc, f, indent=2, ensure_ascii=False)


def main():
    # Define the relevant endpoint patterns
    endpoint_patterns = [
        "auth/login",
        "customers",
        "customers/{customer_id}",
        "customers/groups", 
        "orders",
        "orders/{order_id}/delivery",
        "orders/delivery/{delivery_id}",
        "orders/{order_id}",
        "orders/{order_id}/row",
        "products",
        "products/{id}",
        "products/{id}/stocks",
        "products/base",
        "products/{id}/purchase_price/{supplier}/{stock}",
        "products/stocks/orders",
        "purchaseorders",
        "purchaseorders/{orderNumber}",
        "purchaseorders/{orderNumber}/orderrow"
    ]
    
    # File paths
    input_file = Path("docs/a-swagger-doc.json")
    output_file = Path("docs/lemonrest-filtered-swagger.json")
    
    print(f"Loading swagger documentation from {input_file}...")
    swagger_doc = load_swagger_doc(input_file)
    
    print("Extracting relevant endpoints...")
    filtered_doc = extract_relevant_endpoints(swagger_doc, endpoint_patterns)
    
    print(f"Saving filtered documentation to {output_file}...")
    save_filtered_doc(filtered_doc, output_file)
    
    # Print summary
    total_paths = len(swagger_doc.get("paths", {}))
    filtered_paths = len(filtered_doc["paths"])
    total_definitions = len(swagger_doc.get("definitions", {}))
    filtered_definitions = len(filtered_doc["definitions"])
    
    print(f"\nSummary:")
    print(f"  Original paths: {total_paths}")
    print(f"  Filtered paths: {filtered_paths}")
    print(f"  Original definitions: {total_definitions}")
    print(f"  Filtered definitions: {filtered_definitions}")
    print(f"\nFiltered Swagger documentation saved to: {output_file}")
    
    # List the paths that were included
    print(f"\nIncluded endpoints:")
    for path in sorted(filtered_doc["paths"].keys()):
        methods = list(filtered_doc["paths"][path].keys())
        print(f"  {path} ({', '.join(methods)})")


if __name__ == "__main__":
    main() 