#!/usr/bin/env python3
"""
OpenAPI Specification Validator - Enterprise Edition
Comprehensive validation with strict rules and best practices enforcement
"""

import yaml
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict


class Severity(Enum):
    """Validation issue severity levels"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationStatus(Enum):
    """Overall validation status"""
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"
    CRITICAL_FAILURE = "CRITICAL_FAILURE"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: Severity
    message: str
    path: str = ""
    suggestion: Optional[str] = None
    line_number: Optional[int] = None

    def __str__(self) -> str:
        icons = {
            "CRITICAL": "🔴",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "INFO": "ℹ️"
        }
        icon = icons[self.severity.value]
        result = f"{icon} [{self.severity.value}] {self.message}"
        if self.path:
            result += f"\n   📍 Path: {self.path}"
        if self.line_number:
            result += f"\n   📄 Line: {self.line_number}"
        if self.suggestion:
            result += f"\n   💡 Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationReport:
    """Aggregated validation report"""
    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    seen_issues: Set[Tuple[str, str, str]] = field(default_factory=set, repr=False)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add issue and prevent duplicates"""
        issue_key = (issue.severity.value, issue.message, issue.path)
        if issue_key not in self.seen_issues:
            self.seen_issues.add(issue_key)
            self.issues.append(issue)

    def has_critical(self) -> bool:
        """Check if report contains critical issues"""
        return any(issue.severity == Severity.CRITICAL for issue in self.issues)

    def has_errors(self) -> bool:
        """Check if report contains errors"""
        return any(issue.severity in [Severity.CRITICAL, Severity.ERROR] for issue in self.issues)

    def get_issues_by_severity(self, severity: Severity) -> List[ValidationIssue]:
        """Filter issues by severity"""
        return [issue for issue in self.issues if issue.severity == severity]


class Validator(ABC):
    """Abstract base validator using Strategy pattern"""
    
    @abstractmethod
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        """Validate specific aspect of the specification"""
        pass


class StructureValidator(Validator):
    """Validates basic OpenAPI structure with strict rules"""
    
    REQUIRED_SECTIONS = ['openapi', 'info', 'paths']
    SUPPORTED_VERSIONS = ['3.0.0', '3.0.1', '3.0.2', '3.0.3', '3.1.0']
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        # Validate OpenAPI version (CRITICAL)
        openapi_version = spec.get('openapi')
        if not openapi_version:
            report.add_issue(ValidationIssue(
                Severity.CRITICAL,
                "OpenAPI version is missing - specification is invalid",
                path="openapi",
                suggestion="Add 'openapi: 3.0.3' at the root level"
            ))
        elif str(openapi_version) not in self.SUPPORTED_VERSIONS:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"Unsupported OpenAPI version: {openapi_version}",
                path="openapi",
                suggestion=f"Use one of: {', '.join(self.SUPPORTED_VERSIONS)}"
            ))
        elif str(openapi_version) != '3.0.3':
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                f"OpenAPI version is {openapi_version}, recommended is 3.0.3",
                path="openapi"
            ))
        
        # Validate required sections (CRITICAL)
        for section in self.REQUIRED_SECTIONS:
            if section not in spec:
                report.add_issue(ValidationIssue(
                    Severity.CRITICAL,
                    f"Required section '{section}' is missing",
                    path=section,
                    suggestion=f"Add '{section}' section to the specification"
                ))
        
        # Validate info section
        if 'info' in spec:
            self._validate_info(spec['info'], report)
    
    def _validate_info(self, info: Dict[str, Any], report: ValidationReport) -> None:
        """Validate info section with strict requirements"""
        # Required fields (CRITICAL)
        required_fields = ['title', 'version']
        for field_name in required_fields:
            if field_name not in info:
                report.add_issue(ValidationIssue(
                    Severity.CRITICAL,
                    f"Info section missing required field '{field_name}'",
                    path=f"info.{field_name}"
                ))
        
        # Recommended fields (WARNING)
        recommended_fields = ['description', 'contact', 'license']
        for field_name in recommended_fields:
            if field_name not in info:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Info section missing recommended field '{field_name}'",
                    path=f"info.{field_name}",
                    suggestion="Add for better API documentation"
                ))
        
        # Validate title
        if 'title' in info:
            title = info['title']
            if len(title) < 3:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    "API title is too short (less than 3 characters)",
                    path="info.title"
                ))
            if len(title) > 100:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    "API title is too long (more than 100 characters)",
                    path="info.title"
                ))
        
        # Validate version format
        if 'version' in info:
            version = str(info['version'])
            if not re.match(r'^\d+\.\d+\.\d+', version):
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Version '{version}' doesn't follow semver format",
                    path="info.version",
                    suggestion="Use semantic versioning (e.g., 1.0.0)"
                ))
        
        # Validate contact
        if 'contact' in info:
            contact = info['contact']
            if not isinstance(contact, dict):
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    "Contact must be an object",
                    path="info.contact"
                ))
            elif not any(k in contact for k in ['email', 'url', 'name']):
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    "Contact section is empty",
                    path="info.contact"
                ))
        
        # Validate license
        if 'license' in info:
            license_obj = info['license']
            if not isinstance(license_obj, dict) or 'name' not in license_obj:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    "License must have a 'name' field",
                    path="info.license.name"
                ))
        
        report.metrics['api_title'] = info.get('title', 'N/A')
        report.metrics['api_version'] = info.get('version', 'N/A')


class NamingConventionValidator(Validator):
    """Validates naming conventions and best practices"""
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            # Path naming rules
            if not path.startswith('/'):
                report.add_issue(ValidationIssue(
                    Severity.CRITICAL,
                    f"Path must start with '/': {path}",
                    path=f"paths.{path}"
                ))
            
            # Check for uppercase in path
            if re.search(r'[A-Z]', path):
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Path contains uppercase letters: {path}",
                    path=f"paths.{path}",
                    suggestion="Use lowercase and hyphens for consistency"
                ))
            
            # Check for underscores vs hyphens
            if '_' in path:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Path uses underscores: {path}",
                    path=f"paths.{path}",
                    suggestion="Consider using hyphens instead (RESTful convention)"
                ))
            
            # Check for trailing slash
            if path != '/' and path.endswith('/'):
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Path has trailing slash: {path}",
                    path=f"paths.{path}",
                    suggestion="Remove trailing slash for consistency"
                ))
            
            # Check for path parameters format
            params = re.findall(r'\{([^}]+)\}', path)
            for param in params:
                if not re.match(r'^[a-z][a-zA-Z0-9]*$', param):
                    report.add_issue(ValidationIssue(
                        Severity.WARNING,
                        f"Path parameter '{param}' doesn't follow camelCase convention",
                        path=f"paths.{path}",
                        suggestion="Use camelCase for path parameters"
                    ))
            
            # Validate operation IDs
            if isinstance(methods, dict):
                for method, operation in methods.items():
                    if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']:
                        continue
                    
                    if isinstance(operation, dict) and 'operationId' in operation:
                        op_id = operation['operationId']
                        # Check operationId format
                        if not re.match(r'^[a-z][a-zA-Z0-9]*$', op_id):
                            report.add_issue(ValidationIssue(
                                Severity.WARNING,
                                f"operationId '{op_id}' doesn't follow camelCase convention",
                                path=f"paths.{path}.{method}.operationId",
                                suggestion="Use camelCase (e.g., getUserById)"
                            ))


class PathsValidator(Validator):
    """Validates API paths and operations with strict rules"""
    
    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'}
    SAFE_METHODS = {'get', 'head', 'options'}
    IDEMPOTENT_METHODS = {'get', 'head', 'put', 'delete', 'options'}
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        paths = spec.get('paths', {})
        
        if not paths:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                "No API paths defined",
                path="paths",
                suggestion="Define at least one API endpoint"
            ))
            report.metrics['total_paths'] = 0
            report.metrics['total_operations'] = 0
            return
        
        report.metrics['total_paths'] = len(paths)
        
        # Check for health endpoint (INFO)
        if '/health' not in paths and '/healthz' not in paths:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "Health check endpoint not found",
                path="paths",
                suggestion="Add GET /health or GET /healthz for monitoring"
            ))
        
        # Track operation IDs for uniqueness
        operation_ids = set()
        duplicate_op_ids = set()
        
        # Validate each path
        total_operations = 0
        methods_count = defaultdict(int)
        
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            operations = {m for m in methods.keys() if m.lower() in self.HTTP_METHODS}
            total_operations += len(operations)
            
            if not operations:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Path '{path}' has no HTTP operations defined",
                    path=f"paths.{path}",
                    suggestion="Add at least one HTTP method (GET, POST, etc.)"
                ))
            
            # Check for GET method on collection endpoints
            if not path.endswith('}') and 'get' not in {m.lower() for m in operations}:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Collection endpoint '{path}' doesn't have GET method",
                    path=f"paths.{path}",
                    suggestion="Consider adding GET for listing resources"
                ))
            
            # Validate each operation
            for method in operations:
                methods_count[method.lower()] += 1
                self._validate_operation(
                    path, method, methods[method], report,
                    operation_ids, duplicate_op_ids
                )
        
        # Check for duplicate operation IDs
        if duplicate_op_ids:
            for op_id in duplicate_op_ids:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Duplicate operationId found: '{op_id}'",
                    path="paths",
                    suggestion="Each operation must have a unique operationId"
                ))
        
        report.metrics['total_operations'] = total_operations
        report.metrics['methods_distribution'] = dict(methods_count)
        report.metrics['unique_operation_ids'] = len(operation_ids)
    
    def _validate_operation(
        self,
        path: str,
        method: str,
        operation: Dict[str, Any],
        report: ValidationReport,
        operation_ids: Set[str],
        duplicate_op_ids: Set[str]
    ) -> None:
        """Validate individual operation with strict rules"""
        method_lower = method.lower()
        operation_path = f"paths.{path}.{method}"
        
        # Validate operationId (CRITICAL for code generation)
        operation_id = operation.get('operationId')
        if not operation_id:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"Operation {method.upper()} {path} missing operationId",
                path=operation_path,
                suggestion="Add unique operationId for code generation and documentation"
            ))
        else:
            if operation_id in operation_ids:
                duplicate_op_ids.add(operation_id)
            operation_ids.add(operation_id)
        
        # Validate documentation (WARNING)
        if 'summary' not in operation:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                f"Operation {method.upper()} {path} missing summary",
                path=f"{operation_path}.summary",
                suggestion="Add brief summary for better documentation"
            ))
        
        if 'description' not in operation:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Operation {method.upper()} {path} missing description",
                path=f"{operation_path}.description",
                suggestion="Add detailed description"
            ))
        
        # Validate tags (WARNING)
        if 'tags' not in operation or not operation['tags']:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                f"Operation {method.upper()} {path} missing tags",
                path=f"{operation_path}.tags",
                suggestion="Add tags to organize API documentation"
            ))
        
        # Validate responses (CRITICAL)
        if 'responses' not in operation:
            report.add_issue(ValidationIssue(
                Severity.CRITICAL,
                f"Operation {method.upper()} {path} missing responses",
                path=f"{operation_path}.responses",
                suggestion="Define at least one response"
            ))
        else:
            self._validate_responses(path, method, operation['responses'], report)
        
        # Validate request body for POST/PUT/PATCH
        if method_lower in ['post', 'put', 'patch']:
            if 'requestBody' not in operation:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Operation {method.upper()} {path} missing requestBody",
                    path=f"{operation_path}.requestBody",
                    suggestion=f"{method.upper()} operations typically require a request body"
                ))
            else:
                self._validate_request_body(path, method, operation['requestBody'], report)
        
        # Validate parameters
        if 'parameters' in operation:
            self._validate_parameters(path, method, operation['parameters'], report)
        
        # Check for security (if not health endpoint)
        if not path.startswith('/health') and 'security' not in operation:
            # Only warn if there's no global security
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Operation {method.upper()} {path} has no security defined",
                path=f"{operation_path}.security",
                suggestion="Consider adding authentication requirements"
            ))
    
    def _validate_responses(
        self,
        path: str,
        method: str,
        responses: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Validate response definitions"""
        operation_path = f"paths.{path}.{method}.responses"
        
        # Check for success response
        success_codes = {'200', '201', '202', '204'}
        has_success = any(code in responses for code in success_codes)
        
        if not has_success:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                f"Operation {method.upper()} {path} has no success response (2xx)",
                path=operation_path,
                suggestion="Add at least one 2xx response"
            ))
        
        # Check for error responses
        if '400' not in responses and '404' not in responses:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Operation {method.upper()} {path} missing error responses",
                path=operation_path,
                suggestion="Consider adding 400 (Bad Request) and 404 (Not Found) responses"
            ))
        
        # Check for 500 response
        if '500' not in responses and 'default' not in responses:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Operation {method.upper()} {path} missing server error response",
                path=operation_path,
                suggestion="Add 500 or 'default' response for server errors"
            ))
        
        # Validate each response
        for status_code, response in responses.items():
            if not isinstance(response, dict):
                continue
            
            response_path = f"{operation_path}.{status_code}"
            
            # Check for description (REQUIRED by OpenAPI)
            if 'description' not in response:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Response {status_code} missing required 'description'",
                    path=f"{response_path}.description",
                    suggestion="Add description for this response"
                ))
            
            # Check for content in success responses
            if status_code.startswith('2') and status_code != '204':
                if 'content' not in response:
                    report.add_issue(ValidationIssue(
                        Severity.WARNING,
                        f"Success response {status_code} has no content defined",
                        path=f"{response_path}.content",
                        suggestion="Define response schema if operation returns data"
                    ))
    
    def _validate_request_body(
        self,
        path: str,
        method: str,
        request_body: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Validate request body definition"""
        request_path = f"paths.{path}.{method}.requestBody"
        
        if 'content' not in request_body:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"Request body missing 'content' field",
                path=f"{request_path}.content"
            ))
        else:
            # Check for JSON content type
            if 'application/json' not in request_body['content']:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Request body doesn't include application/json",
                    path=f"{request_path}.content",
                    suggestion="Consider supporting JSON format"
                ))
            
            # Check for schema in content types
            for content_type, content in request_body['content'].items():
                if 'schema' not in content:
                    report.add_issue(ValidationIssue(
                        Severity.WARNING,
                        f"Request body content type '{content_type}' missing schema",
                        path=f"{request_path}.content.{content_type}.schema"
                    ))
        
        # Check if required field is defined
        if 'required' not in request_body:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Request body 'required' field not specified",
                path=f"{request_path}.required",
                suggestion="Explicitly set 'required: true' or 'required: false'"
            ))
    
    def _validate_parameters(
        self,
        path: str,
        method: str,
        parameters: List[Dict[str, Any]],
        report: ValidationReport
    ) -> None:
        """Validate parameter definitions"""
        param_names = set()
        
        for idx, param in enumerate(parameters):
            if not isinstance(param, dict):
                continue
            
            param_path = f"paths.{path}.{method}.parameters[{idx}]"
            
            # Check required fields
            if 'name' not in param:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Parameter missing 'name' field",
                    path=f"{param_path}.name"
                ))
                continue
            
            if 'in' not in param:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Parameter '{param['name']}' missing 'in' field",
                    path=f"{param_path}.in"
                ))
            
            # Check for duplicates
            param_key = (param.get('name'), param.get('in'))
            if param_key in param_names:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Duplicate parameter: {param['name']} in {param.get('in')}",
                    path=param_path
                ))
            param_names.add(param_key)
            
            # Check for description
            if 'description' not in param:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Parameter '{param['name']}' missing description",
                    path=f"{param_path}.description"
                ))
            
            # Check for schema
            if 'schema' not in param:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Parameter '{param['name']}' missing schema",
                    path=f"{param_path}.schema"
                ))


class ComponentsValidator(Validator):
    """Validates components section with strict schema rules"""
    
    RECOMMENDED_SCHEMAS = ['Error', 'Money', 'PaginationMeta', 'ValidationError']
    COMMON_SECURITY_SCHEMES = ['bearerAuth', 'apiKey', 'oauth2']
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        components = spec.get('components', {})
        
        if not components:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                "Components section is missing",
                path="components",
                suggestion="Define reusable components for better maintainability"
            ))
            return
        
        # Validate schemas
        schemas = components.get('schemas', {})
        report.metrics['total_schemas'] = len(schemas)
        
        if not schemas:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                "No schema definitions found",
                path="components.schemas",
                suggestion="Define schemas for request/response validation"
            ))
        else:
            self._validate_schemas(schemas, report)
            
            # Check for recommended schemas
            for schema_name in self.RECOMMENDED_SCHEMAS:
                if schema_name not in schemas:
                    report.add_issue(ValidationIssue(
                        Severity.INFO,
                        f"Recommended schema '{schema_name}' not found",
                        path=f"components.schemas.{schema_name}",
                        suggestion="Consider adding for consistency"
                    ))
        
        # Validate security schemes
        security_schemes = components.get('securitySchemes', {})
        report.metrics['total_security_schemes'] = len(security_schemes)
        
        if not security_schemes:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                "No security schemes defined",
                path="components.securitySchemes",
                suggestion="Define authentication mechanisms"
            ))
        else:
            self._validate_security_schemes(security_schemes, report)
        
        # Validate responses
        if 'responses' in components:
            report.metrics['reusable_responses'] = len(components['responses'])
        
        # Validate parameters
        if 'parameters' in components:
            report.metrics['reusable_parameters'] = len(components['parameters'])
        
        # Validate examples
        if 'examples' in components:
            report.metrics['reusable_examples'] = len(components['examples'])
    
    def _validate_schemas(self, schemas: Dict[str, Any], report: ValidationReport) -> None:
        """Validate schema definitions"""
        for schema_name, schema in schemas.items():
            schema_path = f"components.schemas.{schema_name}"
            
            if not isinstance(schema, dict):
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Schema '{schema_name}' is not a valid object",
                    path=schema_path
                ))
                continue
            
            # Check for type
            if 'type' not in schema and '$ref' not in schema and 'allOf' not in schema and 'oneOf' not in schema and 'anyOf' not in schema:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Schema '{schema_name}' missing 'type' field",
                    path=f"{schema_path}.type",
                    suggestion="Define schema type (object, array, string, etc.)"
                ))
            
            # Check for description
            if 'description' not in schema:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Schema '{schema_name}' missing description",
                    path=f"{schema_path}.description"
                ))
            
            # Validate object schemas
            if schema.get('type') == 'object':
                if 'properties' not in schema:
                    report.add_issue(ValidationIssue(
                        Severity.WARNING,
                        f"Object schema '{schema_name}' has no properties",
                        path=f"{schema_path}.properties",
                        suggestion="Define object properties or use type 'object' with additionalProperties"
                    ))
                
                # Check for required fields
                if 'required' in schema:
                    required_props = set(schema['required'])
                    actual_props = set(schema.get('properties', {}).keys())
                    invalid_required = required_props - actual_props
                    
                    if invalid_required:
                        report.add_issue(ValidationIssue(
                            Severity.ERROR,
                            f"Schema '{schema_name}' has required fields not in properties: {invalid_required}",
                            path=f"{schema_path}.required"
                        ))
            
            # Validate array schemas
            if schema.get('type') == 'array':
                if 'items' not in schema:
                    report.add_issue(ValidationIssue(
                        Severity.ERROR,
                        f"Array schema '{schema_name}' missing 'items' definition",
                        path=f"{schema_path}.items",
                        suggestion="Define items schema for array"
                    ))
            
            # Check for examples
            if 'example' not in schema and 'examples' not in schema:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Schema '{schema_name}' has no examples",
                    path=f"{schema_path}.example",
                    suggestion="Add examples for better documentation"
                ))
    
    def _validate_security_schemes(
        self,
        security_schemes: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Validate security scheme definitions"""
        for scheme_name, scheme in security_schemes.items():
            scheme_path = f"components.securitySchemes.{scheme_name}"
            
            if not isinstance(scheme, dict):
                continue
            
            # Check for required type
            if 'type' not in scheme:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Security scheme '{scheme_name}' missing 'type'",
                    path=f"{scheme_path}.type"
                ))
                continue
            
            scheme_type = scheme['type']
            
            # Validate based on type
            if scheme_type == 'apiKey':
                if 'in' not in scheme:
                    report.add_issue(ValidationIssue(
                        Severity.ERROR,
                        f"apiKey scheme '{scheme_name}' missing 'in' field",
                        path=f"{scheme_path}.in",
                        suggestion="Specify where API key is passed (header, query, cookie)"
                    ))
                if 'name' not in scheme:
                    report.add_issue(ValidationIssue(
                        Severity.ERROR,
                        f"apiKey scheme '{scheme_name}' missing 'name' field",
                        path=f"{scheme_path}.name"
                    ))
            
            elif scheme_type == 'http':
                if 'scheme' not in scheme:
                    report.add_issue(ValidationIssue(
                        Severity.ERROR,
                        f"HTTP scheme '{scheme_name}' missing 'scheme' field",
                        path=f"{scheme_path}.scheme",
                        suggestion="Specify HTTP scheme (basic, bearer, etc.)"
                    ))
            
            elif scheme_type == 'oauth2':
                if 'flows' not in scheme:
                    report.add_issue(ValidationIssue(
                        Severity.ERROR,
                        f"OAuth2 scheme '{scheme_name}' missing 'flows'",
                        path=f"{scheme_path}.flows"
                    ))
            
            # Check for description
            if 'description' not in scheme:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Security scheme '{scheme_name}' missing description",
                    path=f"{scheme_path}.description"
                ))


class SecurityValidator(Validator):
    """Validates security configuration"""
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        # Check for global security
        has_global_security = 'security' in spec
        
        if not has_global_security:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "No global security defined",
                path="security",
                suggestion="Consider adding global security requirements"
            ))
        
        # Count operations with/without security
        paths = spec.get('paths', {})
        secured_ops = 0
        unsecured_ops = 0
        
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            for method, operation in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                
                if not isinstance(operation, dict):
                    continue
                
                # Check if operation has security
                has_security = 'security' in operation or has_global_security
                
                if has_security:
                    secured_ops += 1
                else:
                    unsecured_ops += 1
                    
                    # Warn about unsecured non-health endpoints
                    if not path.startswith('/health'):
                        report.add_issue(ValidationIssue(
                            Severity.WARNING,
                            f"Unsecured operation: {method.upper()} {path}",
                            path=f"paths.{path}.{method}.security",
                            suggestion="Add security requirements"
                        ))
        
        report.metrics['secured_operations'] = secured_ops
        report.metrics['unsecured_operations'] = unsecured_ops


class MetadataValidator(Validator):
    """Validates metadata sections (tags, servers, external docs)"""
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        # Validate tags
        tags = spec.get('tags', [])
        report.metrics['total_tags'] = len(tags)
        
        if not tags:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                "No tags defined",
                path="tags",
                suggestion="Define tags to organize API operations"
            ))
        else:
            self._validate_tags(tags, report)
        
        # Validate servers
        servers = spec.get('servers', [])
        report.metrics['total_servers'] = len(servers)
        
        if not servers:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                "No servers defined",
                path="servers",
                suggestion="Define server URLs for different environments"
            ))
        else:
            self._validate_servers(servers, report)
        
        # Check external documentation
        if 'externalDocs' not in spec:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "External documentation not provided",
                path="externalDocs",
                suggestion="Link to additional API documentation"
            ))
        else:
            self._validate_external_docs(spec['externalDocs'], report)
    
    def _validate_tags(self, tags: List[Dict[str, Any]], report: ValidationReport) -> None:
        """Validate tag definitions"""
        tag_names = set()
        
        for idx, tag in enumerate(tags):
            if not isinstance(tag, dict):
                continue
            
            tag_path = f"tags[{idx}]"
            
            # Check for name
            if 'name' not in tag:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Tag at index {idx} missing 'name'",
                    path=f"{tag_path}.name"
                ))
                continue
            
            tag_name = tag['name']
            
            # Check for duplicates
            if tag_name in tag_names:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Duplicate tag name: '{tag_name}'",
                    path=tag_path
                ))
            tag_names.add(tag_name)
            
            # Check for description
            if 'description' not in tag:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Tag '{tag_name}' missing description",
                    path=f"{tag_path}.description"
                ))
    
    def _validate_servers(self, servers: List[Dict[str, Any]], report: ValidationReport) -> None:
        """Validate server definitions"""
        for idx, server in enumerate(servers):
            if not isinstance(server, dict):
                continue
            
            server_path = f"servers[{idx}]"
            
            # Check for URL (CRITICAL)
            if 'url' not in server:
                report.add_issue(ValidationIssue(
                    Severity.CRITICAL,
                    f"Server at index {idx} missing URL",
                    path=f"{server_path}.url"
                ))
                continue
            
            url = server['url']
            
            # Validate URL format
            if not url.startswith(('http://', 'https://', '/', '{')):
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Server URL may be invalid: {url}",
                    path=f"{server_path}.url",
                    suggestion="URL should start with http://, https://, /, or be templated"
                ))
            
            # Check for description
            if 'description' not in server:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Server '{url}' missing description",
                    path=f"{server_path}.description",
                    suggestion="Add description (e.g., 'Production', 'Staging')"
                ))
            
            # Validate variables if present
            if 'variables' in server:
                for var_name, variable in server['variables'].items():
                    if not isinstance(variable, dict):
                        continue
                    
                    if 'default' not in variable:
                        report.add_issue(ValidationIssue(
                            Severity.ERROR,
                            f"Server variable '{var_name}' missing default value",
                            path=f"{server_path}.variables.{var_name}.default"
                        ))
    
    def _validate_external_docs(
        self,
        external_docs: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Validate external documentation"""
        if 'url' not in external_docs:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                "External docs missing 'url' field",
                path="externalDocs.url"
            ))
        
        if 'description' not in external_docs:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "External docs missing description",
                path="externalDocs.description"
            ))


class ConsistencyValidator(Validator):
    """Validates consistency across the specification"""
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        # Check for unused tags
        defined_tags = {tag['name'] for tag in spec.get('tags', []) if isinstance(tag, dict) and 'name' in tag}
        used_tags = set()
        
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                
                op_tags = operation.get('tags', [])
                used_tags.update(op_tags)
                
                # Check for undefined tags
                for tag in op_tags:
                    if tag not in defined_tags:
                        report.add_issue(ValidationIssue(
                            Severity.WARNING,
                            f"Operation uses undefined tag: '{tag}'",
                            path=f"paths.{path}.{method}.tags",
                            suggestion=f"Add '{tag}' to global tags section"
                        ))
        
        # Check for unused defined tags
        unused_tags = defined_tags - used_tags
        if unused_tags:
            for tag in unused_tags:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Tag '{tag}' is defined but never used",
                    path="tags",
                    suggestion="Remove unused tag or add it to operations"
                ))
        
        # Check for unused schemas
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        
        if schemas:
            self._check_unused_schemas(spec, schemas, report)
        
        # Check for unused security schemes
        security_schemes = components.get('securitySchemes', {})
        if security_schemes:
            self._check_unused_security_schemes(spec, security_schemes, report)
    
    def _check_unused_schemas(
        self,
        spec: Dict[str, Any],
        schemas: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Check for unused schema definitions"""
        # This is a simplified check - could be more thorough
        spec_str = yaml.dump(spec)
        
        for schema_name in schemas.keys():
            ref_string = f"#/components/schemas/{schema_name}"
            # Count references (excluding the definition itself)
            count = spec_str.count(ref_string)
            
            if count <= 1:  # Only the definition itself
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Schema '{schema_name}' appears to be unused",
                    path=f"components.schemas.{schema_name}",
                    suggestion="Remove if truly unused, or document its purpose"
                ))
    
    def _check_unused_security_schemes(
        self,
        spec: Dict[str, Any],
        security_schemes: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Check for unused security schemes"""
        used_schemes = set()
        
        # Check global security
        global_security = spec.get('security', [])
        for sec_req in global_security:
            if isinstance(sec_req, dict):
                used_schemes.update(sec_req.keys())
        
        # Check operation-level security
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                
                op_security = operation.get('security', [])
                for sec_req in op_security:
                    if isinstance(sec_req, dict):
                        used_schemes.update(sec_req.keys())
        
        # Report unused schemes
        for scheme_name in security_schemes.keys():
            if scheme_name not in used_schemes:
                report.add_issue(ValidationIssue(
                    Severity.INFO,
                    f"Security scheme '{scheme_name}' is defined but never used",
                    path=f"components.securitySchemes.{scheme_name}",
                    suggestion="Apply to operations or remove if unnecessary"
                ))


class PerformanceValidator(Validator):
    """Validates performance and pagination best practices"""
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            # Check collection endpoints for pagination
            if not path.endswith('}'):  # Likely a collection endpoint
                if 'get' in methods:
                    operation = methods['get']
                    if isinstance(operation, dict):
                        self._check_pagination(path, operation, report)
        
        # Check for large responses without pagination
        self._check_response_sizes(spec, report)
    
    def _check_pagination(
        self,
        path: str,
        operation: Dict[str, Any],
        report: ValidationReport
    ) -> None:
        """Check if collection endpoint supports pagination"""
        parameters = operation.get('parameters', [])
        param_names = {p.get('name') for p in parameters if isinstance(p, dict)}
        
        pagination_params = {'page', 'limit', 'offset', 'pageSize', 'per_page', 'cursor'}
        has_pagination = bool(pagination_params & param_names)
        
        if not has_pagination:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Collection endpoint GET {path} doesn't support pagination",
                path=f"paths.{path}.get.parameters",
                suggestion="Add pagination parameters (e.g., page, limit, offset)"
            ))
    
    def _check_response_sizes(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        """Check for potentially large responses"""
        # This is a heuristic check
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                
                responses = operation.get('responses', {})
                for status, response in responses.items():
                    if not isinstance(response, dict):
                        continue
                    
                    content = response.get('content', {})
                    for media_type, media in content.items():
                        if not isinstance(media, dict):
                            continue
                        
                        schema = media.get('schema', {})
                        # Check for array responses without pagination mention
                        if schema.get('type') == 'array' and not path.endswith('}'):
                            report.add_issue(ValidationIssue(
                                Severity.INFO,
                                f"Endpoint {method.upper()} {path} returns array - consider pagination",
                                path=f"paths.{path}.{method}.responses.{status}",
                                suggestion="Use pagination for large collections"
                            ))


class OpenAPIValidator:
    """
    Main validator orchestrator using Chain of Responsibility pattern
    Coordinates multiple validators and generates comprehensive reports
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator with configurable strictness
        
        Args:
            strict_mode: Enable all strict validations
        """
        self.strict_mode = strict_mode
        self.validators: List[Validator] = [
            StructureValidator(),
            NamingConventionValidator(),
            PathsValidator(),
            ComponentsValidator(),
            SecurityValidator(),
            MetadataValidator(),
            ConsistencyValidator(),
            PerformanceValidator()
        ]
    
    def validate_file(self, filepath: Path) -> ValidationReport:
        """Validate OpenAPI specification file"""
        report = ValidationReport(status=ValidationStatus.PASSED)
        
        try:
            # Load YAML file
            with open(filepath, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
            
            report.metrics['file_path'] = str(filepath)
            report.metrics['file_size'] = filepath.stat().st_size
            
            # Run all validators
            for validator in self.validators:
                validator.validate(spec, report)
            
            # Determine final status
            if report.has_critical():
                report.status = ValidationStatus.CRITICAL_FAILURE
            elif report.has_errors():
                report.status = ValidationStatus.FAILED
            elif report.get_issues_by_severity(Severity.WARNING):
                report.status = ValidationStatus.PASSED_WITH_WARNINGS
            else:
                report.status = ValidationStatus.PASSED
            
        except yaml.YAMLError as e:
            report.add_issue(ValidationIssue(
                Severity.CRITICAL,
                f"YAML parsing error: {e}",
                suggestion="Check YAML syntax and indentation"
            ))
            report.status = ValidationStatus.CRITICAL_FAILURE
        except FileNotFoundError:
            report.add_issue(ValidationIssue(
                Severity.CRITICAL,
                f"File not found: {filepath}",
                suggestion="Ensure the file path is correct"
            ))
            report.status = ValidationStatus.CRITICAL_FAILURE
        except Exception as e:
            report.add_issue(ValidationIssue(
                Severity.CRITICAL,
                f"Unexpected error: {e}",
                suggestion="Check file format and permissions"
            ))
            report.status = ValidationStatus.CRITICAL_FAILURE
        
        return report


class ReportFormatter:
    """Formats validation reports with beautiful output using Template Method pattern"""
    
    ICONS = {
        ValidationStatus.PASSED: "✅",
        ValidationStatus.PASSED_WITH_WARNINGS: "⚠️",
        ValidationStatus.FAILED: "❌",
        ValidationStatus.CRITICAL_FAILURE: "🔴"
    }
    
    COLORS = {
        'CRITICAL': '\033[91m',  # Red
        'ERROR': '\033[91m',     # Red
        'WARNING': '\033[93m',   # Yellow
        'INFO': '\033[94m',      # Blue
        'RESET': '\033[0m'       # Reset
    }
    
    @staticmethod
    def format(report: ValidationReport, colorize: bool = True) -> str:
        """Format report as readable text"""
        lines = []
        
        # Header
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " OpenAPI Specification Validation Report".center(68) + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")
        
        # Status with color
        status_icon = ReportFormatter.ICONS.get(report.status, "❓")
        status_line = f"{status_icon} Status: {report.status.value}"
        
        if colorize and report.status in [ValidationStatus.FAILED, ValidationStatus.CRITICAL_FAILURE]:
            status_line = f"{ReportFormatter.COLORS['ERROR']}{status_line}{ReportFormatter.COLORS['RESET']}"
        
        lines.append(status_line)
        lines.append("")
        
        # Metrics
        if report.metrics:
            lines.append("📊 Metrics:")
            lines.append("─" * 70)
            
            # Group metrics
            file_metrics = {k: v for k, v in report.metrics.items() if k in ['file_path', 'file_size', 'api_title', 'api_version']}
            count_metrics = {k: v for k, v in report.metrics.items() if k not in file_metrics}
            
            if file_metrics:
                for key, value in file_metrics.items():
                    formatted_key = key.replace('_', ' ').title()
                    lines.append(f"  • {formatted_key}: {value}")
            
            if count_metrics:
                lines.append("")
                for key, value in count_metrics.items():
                    formatted_key = key.replace('_', ' ').title()
                    if isinstance(value, dict):
                        lines.append(f"  • {formatted_key}:")
                        for sub_key, sub_value in value.items():
                            lines.append(f"      - {sub_key}: {sub_value}")
                    else:
                        lines.append(f"  • {formatted_key}: {value}")
            
            lines.append("")
        
        # Issues by severity
        critical = report.get_issues_by_severity(Severity.CRITICAL)
        errors = report.get_issues_by_severity(Severity.ERROR)
        warnings = report.get_issues_by_severity(Severity.WARNING)
        infos = report.get_issues_by_severity(Severity.INFO)
        
        if critical:
            lines.append(f"🔴 Critical Issues ({len(critical)}):")
            lines.append("─" * 70)
            for issue in critical:
                lines.append(str(issue))
                lines.append("")
        
        if errors:
            lines.append(f"❌ Errors ({len(errors)}):")
            lines.append("─" * 70)
            for issue in errors:
                lines.append(str(issue))
                lines.append("")
        
        if warnings:
            lines.append(f"⚠️  Warnings ({len(warnings)}):")
            lines.append("─" * 70)
            for issue in warnings:
                lines.append(str(issue))
                lines.append("")
        
        if infos:
            lines.append(f"ℹ️  Informational ({len(infos)}):")
            lines.append("─" * 70)
            for issue in infos:
                lines.append(str(issue))
                lines.append("")
        
        # Summary
        lines.append("═" * 70)
        summary = (f"Total Issues: {len(report.issues)} "
                  f"(Critical: {len(critical)}, Errors: {len(errors)}, "
                  f"Warnings: {len(warnings)}, Info: {len(infos)})")
        lines.append(summary)
        lines.append("═" * 70)
        
        # Recommendations
        if report.status != ValidationStatus.PASSED:
            lines.append("")
            lines.append("📋 Recommendations:")
            lines.append("─" * 70)
            
            if critical:
                lines.append("  🔴 Fix critical issues immediately - specification is invalid")
            if errors:
                lines.append("  ❌ Fix errors to ensure specification compliance")
            if warnings:
                lines.append("  ⚠️  Review warnings for best practices")
            if infos:
                lines.append("  ℹ️  Consider informational suggestions for improvement")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_json(report: ValidationReport) -> str:
        """Format report as JSON"""
        import json
        
        data = {
            'status': report.status.value,
            'metrics': report.metrics,
            'issues': [
                {
                    'severity': issue.severity.value,
                    'message': issue.message,
                    'path': issue.path,
                    'suggestion': issue.suggestion
                }
                for issue in report.issues
            ]
        }
        
        return json.dumps(data, indent=2)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='OpenAPI Specification Validator - Enterprise Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'file',
        nargs='?',
        default='openapi.yaml',
        help='Path to OpenAPI specification file (default: openapi.yaml)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        default=True,
        help='Enable strict validation mode (default: enabled)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    args = parser.parse_args()
    
    spec_file = Path(args.file)
    
    print("🚀 Starting OpenAPI Validation (Enterprise Mode)...\n")
    
    # Create validator and run validation
    validator = OpenAPIValidator(strict_mode=args.strict)
    report = validator.validate_file(spec_file)
    
    # Format and print report
    if args.json:
        formatted_report = ReportFormatter.format_json(report)
    else:
        formatted_report = ReportFormatter.format(report, colorize=not args.no_color)
    
    print(formatted_report)
    
    # Exit with appropriate code
    exit_code = 0
    if report.status == ValidationStatus.CRITICAL_FAILURE:
        exit_code = 2
    elif report.status == ValidationStatus.FAILED:
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
