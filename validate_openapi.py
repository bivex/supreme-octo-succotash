#!/usr/bin/env python3
"""
OpenAPI Specification Validator
Enterprise-grade validation with extensible architecture and comprehensive reporting
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class Severity(Enum):
    """Validation issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationStatus(Enum):
    """Overall validation status"""
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: Severity
    message: str
    path: str = ""
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[self.severity.value]
        result = f"{icon} [{self.severity.value}] {self.message}"
        if self.path:
            result += f"\n   Path: {self.path}"
        if self.suggestion:
            result += f"\n   💡 Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationReport:
    """Aggregated validation report"""
    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add issue and prevent duplicates"""
        if not any(
            existing.severity == issue.severity and 
            existing.message == issue.message and 
            existing.path == issue.path 
            for existing in self.issues
        ):
            self.issues.append(issue)

    def has_errors(self) -> bool:
        """Check if report contains errors"""
        return any(issue.severity == Severity.ERROR for issue in self.issues)

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
    """Validates basic OpenAPI structure"""
    
    REQUIRED_SECTIONS = ['openapi', 'info', 'paths']
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        # Validate OpenAPI version
        openapi_version = spec.get('openapi')
        if not openapi_version:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                "OpenAPI version is missing",
                path="openapi",
                suggestion="Add 'openapi: 3.0.3' at the root level"
            ))
        elif openapi_version != '3.0.3':
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                f"OpenAPI version is {openapi_version}, expected 3.0.3",
                path="openapi"
            ))
        
        # Validate required sections
        for section in self.REQUIRED_SECTIONS:
            if section not in spec:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Required section '{section}' is missing",
                    path=section,
                    suggestion=f"Add '{section}' section to the specification"
                ))
        
        # Validate info section
        if 'info' in spec:
            self._validate_info(spec['info'], report)
    
    def _validate_info(self, info: Dict[str, Any], report: ValidationReport) -> None:
        """Validate info section"""
        required_fields = ['title', 'version']
        for field_name in required_fields:
            if field_name not in info:
                report.add_issue(ValidationIssue(
                    Severity.ERROR,
                    f"Info section missing required field '{field_name}'",
                    path=f"info.{field_name}"
                ))
        
        if 'description' not in info:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "Consider adding a description to the info section",
                path="info.description"
            ))
        
        report.metrics['api_title'] = info.get('title', 'N/A')
        report.metrics['api_version'] = info.get('version', 'N/A')


class PathsValidator(Validator):
    """Validates API paths and operations"""
    
    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'}
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        paths = spec.get('paths', {})
        
        if not paths:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                "No API paths defined",
                path="paths",
                suggestion="Define at least one API endpoint"
            ))
            report.metrics['total_paths'] = 0
            report.metrics['total_operations'] = 0
            return
        
        report.metrics['total_paths'] = len(paths)
        
        # Check for health endpoint
        if '/health' not in paths:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "Health check endpoint not found",
                path="paths./health",
                suggestion="Consider adding GET /health for monitoring"
            ))
        
        # Validate each path
        total_operations = 0
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            operations = {m for m in methods.keys() if m.lower() in self.HTTP_METHODS}
            total_operations += len(operations)
            
            if not operations:
                report.add_issue(ValidationIssue(
                    Severity.WARNING,
                    f"Path '{path}' has no HTTP operations defined",
                    path=f"paths.{path}"
                ))
            
            # Validate each operation
            for method in operations:
                self._validate_operation(path, method, methods[method], report)
        
        report.metrics['total_operations'] = total_operations
    
    def _validate_operation(
        self, 
        path: str, 
        method: str, 
        operation: Dict[str, Any], 
        report: ValidationReport
    ) -> None:
        """Validate individual operation"""
        operation_id = operation.get('operationId')
        if not operation_id:
            report.add_issue(ValidationIssue(
                Severity.WARNING,
                f"Operation {method.upper()} {path} missing operationId",
                path=f"paths.{path}.{method}",
                suggestion="Add unique operationId for better code generation"
            ))
        
        if 'summary' not in operation and 'description' not in operation:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                f"Operation {method.upper()} {path} has no documentation",
                path=f"paths.{path}.{method}",
                suggestion="Add summary or description"
            ))
        
        if 'responses' not in operation:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"Operation {method.upper()} {path} missing responses",
                path=f"paths.{path}.{method}.responses"
            ))


class ComponentsValidator(Validator):
    """Validates components section"""
    
    RECOMMENDED_SCHEMAS = ['Error', 'Money']
    
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
                Severity.INFO,
                "No schema definitions found",
                path="components.schemas"
            ))
        else:
            # Check for recommended schemas
            for schema_name in self.RECOMMENDED_SCHEMAS:
                if schema_name not in schemas:
                    report.add_issue(ValidationIssue(
                        Severity.INFO,
                        f"Recommended schema '{schema_name}' not found",
                        path=f"components.schemas.{schema_name}"
                    ))
        
        # Validate security schemes
        security_schemes = components.get('securitySchemes', {})
        report.metrics['total_security_schemes'] = len(security_schemes)
        
        if not security_schemes:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "No security schemes defined",
                path="components.securitySchemes",
                suggestion="Define authentication mechanisms if API requires security"
            ))


class MetadataValidator(Validator):
    """Validates metadata sections (tags, servers, external docs)"""
    
    def validate(self, spec: Dict[str, Any], report: ValidationReport) -> None:
        # Validate tags
        tags = spec.get('tags', [])
        report.metrics['total_tags'] = len(tags)
        
        if not tags:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "No tags defined",
                path="tags",
                suggestion="Define tags to organize API operations"
            ))
        
        # Validate servers
        servers = spec.get('servers', [])
        report.metrics['total_servers'] = len(servers)
        
        if not servers:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "No servers defined",
                path="servers",
                suggestion="Define server URLs for different environments"
            ))
        else:
            for idx, server in enumerate(servers):
                if 'url' not in server:
                    report.add_issue(ValidationIssue(
                        Severity.ERROR,
                        f"Server at index {idx} missing URL",
                        path=f"servers[{idx}].url"
                    ))
        
        # Check external documentation
        if 'externalDocs' not in spec:
            report.add_issue(ValidationIssue(
                Severity.INFO,
                "External documentation not provided",
                path="externalDocs"
            ))


class OpenAPIValidator:
    """
    Main validator orchestrator using Chain of Responsibility pattern
    Coordinates multiple validators and generates comprehensive reports
    """
    
    def __init__(self):
        self.validators: List[Validator] = [
            StructureValidator(),
            PathsValidator(),
            ComponentsValidator(),
            MetadataValidator()
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
            if report.has_errors():
                report.status = ValidationStatus.FAILED
            elif report.get_issues_by_severity(Severity.WARNING):
                report.status = ValidationStatus.PASSED_WITH_WARNINGS
            else:
                report.status = ValidationStatus.PASSED
            
        except yaml.YAMLError as e:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"YAML parsing error: {e}",
                suggestion="Check YAML syntax and indentation"
            ))
            report.status = ValidationStatus.FAILED
        except FileNotFoundError:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"File not found: {filepath}",
                suggestion="Ensure the file path is correct"
            ))
            report.status = ValidationStatus.FAILED
        except Exception as e:
            report.add_issue(ValidationIssue(
                Severity.ERROR,
                f"Unexpected error: {e}"
            ))
            report.status = ValidationStatus.FAILED
        
        return report


class ReportFormatter:
    """Formats validation reports with beautiful output using Template Method pattern"""
    
    ICONS = {
        ValidationStatus.PASSED: "✅",
        ValidationStatus.PASSED_WITH_WARNINGS: "⚠️",
        ValidationStatus.FAILED: "❌"
    }
    
    @staticmethod
    def format(report: ValidationReport) -> str:
        """Format report as readable text"""
        lines = []
        
        # Header
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " OpenAPI Specification Validation Report".center(68) + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")
        
        # Status
        status_icon = ReportFormatter.ICONS.get(report.status, "❓")
        lines.append(f"{status_icon} Status: {report.status.value}")
        lines.append("")
        
        # Metrics
        if report.metrics:
            lines.append("📊 Metrics:")
            lines.append("─" * 70)
            for key, value in report.metrics.items():
                formatted_key = key.replace('_', ' ').title()
                lines.append(f"  • {formatted_key}: {value}")
            lines.append("")
        
        # Issues by severity
        errors = report.get_issues_by_severity(Severity.ERROR)
        warnings = report.get_issues_by_severity(Severity.WARNING)
        infos = report.get_issues_by_severity(Severity.INFO)
        
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
        lines.append(f"Total Issues: {len(report.issues)} " +
                    f"(Errors: {len(errors)}, Warnings: {len(warnings)}, Info: {len(infos)})")
        lines.append("═" * 70)
        
        return "\n".join(lines)


def main():
    """Main entry point"""
    spec_file = Path('openapi.yaml')
    
    print("🚀 Starting OpenAPI Validation...\n")
    
    # Create validator and run validation
    validator = OpenAPIValidator()
    report = validator.validate_file(spec_file)
    
    # Format and print report
    formatted_report = ReportFormatter.format(report)
    print(formatted_report)
    
    # Exit with appropriate code
    exit_code = 0 if report.status != ValidationStatus.FAILED else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()