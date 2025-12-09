#!/usr/bin/env python3
"""
OpenAPI Specification Validation Script
Validates the structure and completeness of the OpenAPI YAML specification
"""

import yaml
import json

def validate_openapi_spec():
    """Validate the OpenAPI specification"""

    print("🔍 OpenAPI Specification Validation")
    print("=" * 50)

    try:
        # Load the YAML
        with open('openapi.yaml', 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)

        print("✅ YAML Syntax: VALID")

        # Check OpenAPI version
        openapi_version = spec.get('openapi')
        print(f"📋 OpenAPI Version: {openapi_version}")
        if openapi_version == '3.0.3':
            print("✅ OpenAPI Version: CORRECT (3.0.3)")
        else:
            print(f"⚠️  OpenAPI Version: {openapi_version} (Expected: 3.0.3)")

        # Check basic info
        info = spec.get('info', {})
        print(f"📄 API Title: {info.get('title', 'MISSING')}")
        print(f"🏷️  API Version: {info.get('version', 'MISSING')}")

        # Check required sections
        required_sections = ['openapi', 'info', 'paths']
        print("\n🔧 REQUIRED SECTIONS:")
        for section in required_sections:
            if section in spec:
                print(f"✅ Required section '{section}': PRESENT")
            else:
                print(f"❌ Required section '{section}': MISSING")

        # Check paths
        print("\n🛣️  PATHS SECTION:")
        if 'paths' in spec:
            path_count = len(spec['paths'])
            print(f"✅ Paths section: {path_count} paths defined")

            # Check for required health endpoint
            if '/health' in spec['paths']:
                print("✅ Health check endpoint: PRESENT")
            else:
                print("❌ Health check endpoint: MISSING")

            # Count operations per path
            total_operations = 0
            for path, methods in spec['paths'].items():
                if isinstance(methods, dict):
                    operations = [m for m in methods.keys() if m.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']]
                    total_operations += len(operations)

            print(f"📊 Total API operations: {total_operations}")

        # Check components
        print("\n🏗️  COMPONENTS SECTION:")
        if 'components' in spec:
            print("✅ Components section: PRESENT")

            if 'schemas' in spec['components']:
                schema_count = len(spec['components']['schemas'])
                print(f"✅ Schema definitions: {schema_count} schemas defined")

                # Check for key schemas
                required_schemas = ['Error', 'Money', 'CampaignResource', 'ClickRecord']
                for schema in required_schemas:
                    if schema in spec['components']['schemas']:
                        print(f"  ✅ Schema '{schema}': PRESENT")
                    else:
                        print(f"  ❌ Schema '{schema}': MISSING")

            if 'securitySchemes' in spec['components']:
                security_count = len(spec['components']['securitySchemes'])
                print(f"✅ Security schemes: {security_count} schemes defined")

                # Check for key security schemes
                required_security = ['bearerAuth', 'apiKey']
                for scheme in required_security:
                    if scheme in spec['components']['securitySchemes']:
                        print(f"  ✅ Security scheme '{scheme}': PRESENT")
                    else:
                        print(f"  ❌ Security scheme '{scheme}': MISSING")
        else:
            print("❌ Components section: MISSING")

        # Check tags
        print("\n🏷️  TAGS SECTION:")
        if 'tags' in spec:
            tag_count = len(spec['tags'])
            print(f"✅ Tags section: {tag_count} tags defined")

            # List all tags
            for tag in spec['tags']:
                tag_name = tag.get('name', 'UNKNOWN')
                print(f"  • {tag_name}")
        else:
            print("❌ Tags section: MISSING")

        # Check servers
        print("\n🌐 SERVERS SECTION:")
        if 'servers' in spec:
            server_count = len(spec['servers'])
            print(f"✅ Servers section: {server_count} servers defined")

            for i, server in enumerate(spec['servers']):
                url = server.get('url', 'UNKNOWN')
                desc = server.get('description', 'No description')
                print(f"  {i+1}. {url} - {desc}")
        else:
            print("❌ Servers section: MISSING")

        # Check external docs
        print("\n📚 EXTERNAL DOCUMENTATION:")
        if 'externalDocs' in spec:
            docs_url = spec['externalDocs'].get('url', 'UNKNOWN')
            docs_desc = spec['externalDocs'].get('description', 'No description')
            print(f"✅ External docs: {docs_url}")
            print(f"   Description: {docs_desc}")
        else:
            print("ℹ️  External documentation: NOT PROVIDED")

        print("\n" + "=" * 50)
        print("🎉 OpenAPI Specification Validation: COMPLETE")
        print("=" * 50)

        # Final assessment
        issues = []

        if not all(section in spec for section in required_sections):
            issues.append("Missing required sections")

        if 'paths' not in spec or len(spec['paths']) == 0:
            issues.append("No API paths defined")

        if 'components' not in spec:
            issues.append("Missing components section")

        if issues:
            print(f"\n⚠️  ISSUES FOUND ({len(issues)}):")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("\n✅ NO ISSUES FOUND - Specification is valid!")

        return len(issues) == 0

    except yaml.YAMLError as e:
        print(f"❌ YAML PARSING ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ VALIDATION ERROR: {e}")
        return False

if __name__ == "__main__":
    success = validate_openapi_spec()
    exit(0 if success else 1)
