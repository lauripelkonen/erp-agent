#!/usr/bin/env python3
"""
Script to convert Swagger 2.0 documentation to OpenAPI 3.x format.
This ensures compatibility with modern API tools and MCP server generators.
"""

import json
import copy
from pathlib import Path


def load_swagger_doc(file_path):
    """Load the swagger 2.0 documentation."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_to_openapi3(swagger_doc):
    """
    Convert Swagger 2.0 specification to OpenAPI 3.x format.
    
    Args:
        swagger_doc: Swagger 2.0 specification
    
    Returns:
        OpenAPI 3.x specification
    """
    openapi_doc = {
        "openapi": "3.0.3",
        "info": copy.deepcopy(swagger_doc["info"]),
        "servers": [
            {
                "url": f"{swagger_doc['schemes'][0]}://{swagger_doc['host']}{swagger_doc['basePath']}",
                "description": "LemonRest API Server"
            }
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization"
                },
                "SessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session"
                }
            }
        }
    }
    
    # Convert definitions to components/schemas
    if "definitions" in swagger_doc:
        for def_name, def_schema in swagger_doc["definitions"].items():
            openapi_doc["components"]["schemas"][def_name] = convert_schema(def_schema)
    
    # Convert paths
    for path, path_item in swagger_doc["paths"].items():
        openapi_doc["paths"][path] = convert_path_item(path_item)
    
    return openapi_doc


def convert_schema(schema):
    """Convert a Swagger 2.0 schema to OpenAPI 3.x format."""
    if not isinstance(schema, dict):
        return schema
    
    converted = copy.deepcopy(schema)
    
    # Update $ref paths
    if "$ref" in converted:
        ref_path = converted["$ref"]
        if ref_path.startswith("#/definitions/"):
            converted["$ref"] = ref_path.replace("#/definitions/", "#/components/schemas/")
    
    # Recursively convert nested schemas
    for key, value in converted.items():
        if isinstance(value, dict):
            converted[key] = convert_schema(value)
        elif isinstance(value, list):
            converted[key] = [convert_schema(item) for item in value]
    
    return converted


def convert_path_item(path_item):
    """Convert a Swagger 2.0 path item to OpenAPI 3.x format."""
    converted_path_item = {}
    
    for method, operation in path_item.items():
        if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
            converted_path_item[method] = convert_operation(operation)
        else:
            # Copy non-HTTP method properties as-is
            converted_path_item[method] = operation
    
    return converted_path_item


def convert_operation(operation):
    """Convert a Swagger 2.0 operation to OpenAPI 3.x format."""
    converted_op = {
        "summary": operation.get("summary", ""),
        "description": operation.get("description", ""),
        "operationId": operation.get("operationId"),
        "tags": operation.get("tags", []),
        "parameters": [],
        "responses": {}
    }
    
    # Remove None values
    converted_op = {k: v for k, v in converted_op.items() if v is not None}
    
    # Convert parameters
    body_schema = None
    form_parameters = []
    
    for param in operation.get("parameters", []):
        if param.get("in") == "body":
            body_schema = param.get("schema")
        elif param.get("in") == "formData":
            form_parameters.append(param)
        else:
            # Query, path, header parameters
            converted_param = convert_parameter(param)
            if converted_param:
                converted_op["parameters"].append(converted_param)
    
    # Handle request body (from body and formData parameters)
    if body_schema or form_parameters:
        converted_op["requestBody"] = convert_request_body(body_schema, form_parameters, operation.get("consumes", []))
    
    # Convert responses
    for status_code, response in operation.get("responses", {}).items():
        converted_op["responses"][status_code] = convert_response(response, operation.get("produces", []))
    
    # Add security if the operation requires authentication
    if operation.get("security") or should_require_auth(operation):
        converted_op["security"] = [
            {"ApiKeyAuth": []},
            {"SessionAuth": []}
        ]
    
    return converted_op


def convert_parameter(param):
    """Convert a Swagger 2.0 parameter to OpenAPI 3.x format."""
    if param.get("in") in ["body", "formData"]:
        return None  # These are handled separately
    
    converted_param = {
        "name": param["name"],
        "in": param["in"],
        "required": param.get("required", False),
        "description": param.get("description", "")
    }
    
    # Convert schema
    schema = {}
    if "type" in param:
        schema["type"] = param["type"]
    if "format" in param:
        schema["format"] = param["format"]
    if "items" in param:
        schema["items"] = convert_schema(param["items"])
    if "enum" in param:
        schema["enum"] = param["enum"]
    if "collectionFormat" in param:
        if param["collectionFormat"] == "multi":
            converted_param["style"] = "form"
            converted_param["explode"] = True
    
    converted_param["schema"] = schema
    
    return converted_param


def convert_request_body(body_schema, form_parameters, consumes):
    """Convert Swagger 2.0 body/formData parameters to OpenAPI 3.x requestBody."""
    request_body = {
        "required": True,
        "content": {}
    }
    
    if body_schema:
        # JSON body
        media_types = ["application/json"] if not consumes else [ct for ct in consumes if "json" in ct]
        if not media_types:
            media_types = ["application/json"]
        
        for media_type in media_types:
            request_body["content"][media_type] = {
                "schema": convert_schema(body_schema)
            }
    
    if form_parameters:
        # Form data
        properties = {}
        required = []
        
        for param in form_parameters:
            prop_schema = {"type": param.get("type", "string")}
            if "format" in param:
                prop_schema["format"] = param["format"]
            if "description" in param:
                prop_schema["description"] = param["description"]
            
            properties[param["name"]] = prop_schema
            
            if param.get("required"):
                required.append(param["name"])
        
        form_schema = {
            "type": "object",
            "properties": properties
        }
        if required:
            form_schema["required"] = required
        
        # Determine content type
        media_type = "application/x-www-form-urlencoded"
        if any(param.get("type") == "file" for param in form_parameters):
            media_type = "multipart/form-data"
        
        request_body["content"][media_type] = {
            "schema": form_schema
        }
    
    return request_body


def convert_response(response, produces):
    """Convert a Swagger 2.0 response to OpenAPI 3.x format."""
    converted_response = {
        "description": response.get("description", "")
    }
    
    if "schema" in response:
        content = {}
        media_types = produces if produces else ["application/json"]
        
        for media_type in media_types:
            content[media_type] = {
                "schema": convert_schema(response["schema"])
            }
        
        converted_response["content"] = content
    
    # Convert headers if present
    if "headers" in response:
        converted_response["headers"] = {}
        for header_name, header_def in response["headers"].items():
            converted_response["headers"][header_name] = {
                "schema": {
                    "type": header_def.get("type", "string"),
                    "format": header_def.get("format")
                },
                "description": header_def.get("description", "")
            }
    
    return converted_response


def should_require_auth(operation):
    """Determine if an operation should require authentication based on its path/tags."""
    # Most operations require auth except login
    operation_id = operation.get("operationId", "")
    if "login" in operation_id.lower() or "Login" in operation_id:
        return False
    return True


def save_openapi_doc(openapi_doc, output_path):
    """Save the OpenAPI 3.x documentation to a file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_doc, f, indent=2, ensure_ascii=False)


def main():
    # File paths
    input_file = Path("docs/lemonrest-filtered-swagger.json")
    output_file = Path("docs/lemonrest-openapi3.json")
    
    print(f"Loading Swagger 2.0 documentation from {input_file}...")
    swagger_doc = load_swagger_doc(input_file)
    
    print("Converting to OpenAPI 3.x format...")
    openapi_doc = convert_to_openapi3(swagger_doc)
    
    print(f"Saving OpenAPI 3.x documentation to {output_file}...")
    save_openapi_doc(openapi_doc, output_file)
    
    # Print summary
    swagger_paths = len(swagger_doc.get("paths", {}))
    openapi_paths = len(openapi_doc["paths"])
    swagger_definitions = len(swagger_doc.get("definitions", {}))
    openapi_schemas = len(openapi_doc["components"]["schemas"])
    
    print(f"\nConversion Summary:")
    print(f"  Swagger 2.0 → OpenAPI 3.0.3")
    print(f"  Paths: {swagger_paths} → {openapi_paths}")
    print(f"  Definitions/Schemas: {swagger_definitions} → {openapi_schemas}")
    print(f"  Server: {openapi_doc['servers'][0]['url']}")
    print(f"\nOpenAPI 3.x documentation saved to: {output_file}")
    
    # List some key features
    print(f"\nKey Features Added:")
    print(f"  ✓ OpenAPI 3.0.3 format")
    print(f"  ✓ Server configuration")
    print(f"  ✓ Request body schemas (from body/formData)")
    print(f"  ✓ Response content types")
    print(f"  ✓ Security schemes (API key & session)")
    print(f"  ✓ Updated $ref paths to components/schemas")


if __name__ == "__main__":
    main() 