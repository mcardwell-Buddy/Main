"""
Tests for Artifact Schema Versioning System (Phase 4a)

Tests the artifact schema evolution and migration framework:
- Schema registration and discovery
- Schema validation
- Migration path finding and execution
- Backward compatibility
- Version detection and inference
"""

import json
from typing import Dict, Any
import pytest

from Back_End.artifact_schema_versioning import (
    ArtifactSchemaRegistry,
    ArtifactSchemaValidator,
    SchemaMetadata,
    SchemaMigration,
    SchemaVersion,
    get_schema_registry,
)


class TestSchemaRegistration:
    """Test schema registration and discovery"""

    def test_schema_registry_initialization(self):
        """Verify schema registry initializes with all builtin schemas"""
        registry = ArtifactSchemaRegistry()
        
        # Should have all 4 built-in schemas
        assert len(registry.schemas) == 4, "Should have 4 built-in schemas"
        assert "1.0" in registry.schemas, "Should have v1.0"
        assert "2.0" in registry.schemas, "Should have v2.0"
        assert "3.0" in registry.schemas, "Should have v3.0"
        assert "4.0" in registry.schemas, "Should have v4.0"

    def test_get_schema_metadata(self):
        """Verify retrieving schema metadata"""
        registry = ArtifactSchemaRegistry()
        
        schema = registry.get_schema("1.0")
        assert schema is not None
        assert schema.version == "1.0"
        assert schema.description == "Initial artifact schema with basic metadata"
        
        schema_4 = registry.get_schema("4.0")
        assert schema_4 is not None
        assert "cost tracking" in schema_4.description.lower()

    def test_nonexistent_schema_returns_none(self):
        """Verify getting nonexistent schema returns None"""
        registry = ArtifactSchemaRegistry()
        
        schema = registry.get_schema("99.0")
        assert schema is None

    def test_schema_metadata_fields(self):
        """Verify schema metadata contains expected fields"""
        registry = ArtifactSchemaRegistry()
        
        schema = registry.get_schema("2.0")
        assert hasattr(schema, "version")
        assert hasattr(schema, "released_at")
        assert hasattr(schema, "description")
        assert hasattr(schema, "breaking_changes")
        assert hasattr(schema, "deprecated_fields")
        assert hasattr(schema, "new_fields")
        assert hasattr(schema, "migration_required")
        assert hasattr(schema, "compatible_with")


class TestSchemaMigration:
    """Test schema migration path finding and execution"""

    def test_direct_migration_exists(self):
        """Verify direct migrations are registered"""
        registry = ArtifactSchemaRegistry()
        
        migration = registry.get_migration("1.0", "2.0")
        assert migration is not None
        assert migration.from_version == "1.0"
        assert migration.to_version == "2.0"
        assert migration.rollback_capable is True

    def test_nonexistent_migration_returns_none(self):
        """Verify nonexistent migration returns None"""
        registry = ArtifactSchemaRegistry()
        
        migration = registry.get_migration("4.0", "1.0")  # Backward migration
        assert migration is None

    def test_migration_path_single_step(self):
        """Verify finding single-step migration"""
        registry = ArtifactSchemaRegistry()
        
        path = registry.get_migration_path("1.0", "2.0")
        assert len(path) == 1
        assert path[0].from_version == "1.0"
        assert path[0].to_version == "2.0"

    def test_migration_path_multiple_steps(self):
        """Verify finding multi-step migration path"""
        registry = ArtifactSchemaRegistry()
        
        path = registry.get_migration_path("1.0", "4.0")
        assert len(path) == 3, "Should find 3 migrations: 1→2, 2→3, 3→4"
        assert path[0].from_version == "1.0"
        assert path[0].to_version == "2.0"
        assert path[1].from_version == "2.0"
        assert path[1].to_version == "3.0"
        assert path[2].from_version == "3.0"
        assert path[2].to_version == "4.0"

    def test_same_version_returns_empty_path(self):
        """Verify same version returns empty migration path"""
        registry = ArtifactSchemaRegistry()
        
        path = registry.get_migration_path("2.0", "2.0")
        assert len(path) == 0

    def test_nonexistent_path_returns_empty(self):
        """Verify nonexistent path returns empty list"""
        registry = ArtifactSchemaRegistry()
        
        # No path from 4.0 backward to 1.0
        path = registry.get_migration_path("4.0", "1.0")
        assert len(path) == 0


class TestArtifactMigration:
    """Test artifact migration between schema versions"""

    def test_migrate_1_0_to_2_0_adds_learning_fields(self):
        """Verify migration 1.0→2.0 adds learning fields"""
        registry = ArtifactSchemaRegistry()
        
        artifact_v1 = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "metrics": {"confidence_score": 0.85}
        }
        
        success, migrated, msg = registry.migrate_artifact(artifact_v1, "1.0", "2.0")
        
        assert success is True
        assert "learning_insights" in migrated
        assert "confidence_score" in migrated
        assert migrated["schema_version"] == "2.0"
        assert migrated["confidence_score"] == 0.85  # From metrics

    def test_migrate_2_0_to_3_0_adds_relationships(self):
        """Verify migration 2.0→3.0 adds relationship fields"""
        registry = ArtifactSchemaRegistry()
        
        artifact_v2 = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "confidence_score": 0.85,
            "learning_insights": []
        }
        
        success, migrated, msg = registry.migrate_artifact(artifact_v2, "2.0", "3.0")
        
        assert success is True
        assert "relationships" in migrated
        assert "relationship_metadata" in migrated
        assert isinstance(migrated["relationships"], list)
        assert migrated["schema_version"] == "3.0"

    def test_migrate_3_0_to_4_0_adds_cost_fields(self):
        """Verify migration 3.0→4.0 adds cost tracking"""
        registry = ArtifactSchemaRegistry()
        
        artifact_v3 = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "relationships": [],
            "relationship_metadata": {}
        }
        
        success, migrated, msg = registry.migrate_artifact(artifact_v3, "3.0", "4.0")
        
        assert success is True
        assert "cost_estimate" in migrated
        assert "cost_actual" in migrated
        assert "cost_variance" in migrated
        assert migrated["cost_estimate"] == 0.0
        assert migrated["schema_version"] == "4.0"

    def test_migrate_full_chain_1_0_to_4_0(self):
        """Verify full migration chain from 1.0 to 4.0"""
        registry = ArtifactSchemaRegistry()
        
        artifact_v1 = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "metrics": {"confidence_score": 0.95}
        }
        
        success, migrated, msg = registry.migrate_artifact(artifact_v1, "1.0", "4.0")
        
        assert success is True
        assert migrated["schema_version"] == "4.0"
        # Verify all fields are present
        assert "artifact_id" in migrated
        assert "learning_insights" in migrated
        assert "relationships" in migrated
        assert "cost_estimate" in migrated
        assert migrated["confidence_score"] == 0.95

    def test_same_version_migration_returns_unchanged(self):
        """Verify migrating to same version returns unchanged artifact"""
        registry = ArtifactSchemaRegistry()
        
        artifact = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published"
        }
        
        success, migrated, msg = registry.migrate_artifact(artifact, "2.0", "2.0")
        
        assert success is True
        assert migrated == artifact
        assert msg == "No migration needed"


class TestSchemaValidation:
    """Test schema validation"""

    def test_validate_v1_0_requires_fields(self):
        """Verify v1.0 validation requires core fields"""
        artifact_valid = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z"
        }
        
        registry = ArtifactSchemaRegistry()
        is_valid, errors = registry.validate_artifact(artifact_valid, "1.0")
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_v1_0_rejects_missing_fields(self):
        """Verify v1.0 validation rejects missing required fields"""
        artifact_invalid = {
            "artifact_id": "a-1",
            "artifact_type": "report"
            # Missing status and created_at
        }
        
        registry = ArtifactSchemaRegistry()
        is_valid, errors = registry.validate_artifact(artifact_invalid, "1.0")
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_v2_0_confidence_range(self):
        """Verify v2.0 validation checks confidence score range"""
        artifact_invalid = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "confidence_score": 1.5  # Invalid: > 1.0
        }
        
        registry = ArtifactSchemaRegistry()
        is_valid, errors = registry.validate_artifact(artifact_invalid, "2.0")
        assert is_valid is False
        assert any("confidence_score" in e for e in errors)

    def test_validate_v3_0_relationships_format(self):
        """Verify v3.0 validation checks relationships format"""
        artifact_invalid = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "relationships": "not_a_list"  # Invalid: should be list
        }
        
        registry = ArtifactSchemaRegistry()
        is_valid, errors = registry.validate_artifact(artifact_invalid, "3.0")
        assert is_valid is False
        assert any("relationships" in e for e in errors)

    def test_validate_v4_0_cost_fields(self):
        """Verify v4.0 validation checks cost field types"""
        artifact_invalid = {
            "artifact_id": "a-1",
            "artifact_type": "report",
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "cost_estimate": -100  # Invalid: negative
        }
        
        registry = ArtifactSchemaRegistry()
        is_valid, errors = registry.validate_artifact(artifact_invalid, "4.0")
        assert is_valid is False
        assert any("cost_estimate" in e for e in errors)


class TestSchemaSingleton:
    """Test schema registry singleton"""

    def test_get_schema_registry_singleton(self):
        """Verify get_schema_registry returns singleton"""
        registry1 = get_schema_registry()
        registry2 = get_schema_registry()
        
        assert registry1 is registry2, "Should return same instance"

    def test_singleton_has_validators(self):
        """Verify singleton has all validators registered"""
        registry = get_schema_registry()
        
        assert "1.0" in registry.validators
        assert "2.0" in registry.validators
        assert "3.0" in registry.validators
        assert "4.0" in registry.validators


class TestBackwardCompatibility:
    """Test backward compatibility across schema versions"""

    def test_v2_0_compatible_with_v1_0(self):
        """Verify v2.0 schema is compatible with v1.0"""
        registry = ArtifactSchemaRegistry()
        
        schema_v2 = registry.get_schema("2.0")
        assert "1.0" in schema_v2.compatible_with

    def test_v3_0_compatible_with_v1_0_and_v2_0(self):
        """Verify v3.0 is compatible with earlier versions"""
        registry = ArtifactSchemaRegistry()
        
        schema_v3 = registry.get_schema("3.0")
        assert "1.0" in schema_v3.compatible_with
        assert "2.0" in schema_v3.compatible_with

    def test_v4_0_compatible_with_all_earlier(self):
        """Verify v4.0 is compatible with all earlier versions"""
        registry = ArtifactSchemaRegistry()
        
        schema_v4 = registry.get_schema("4.0")
        assert "1.0" in schema_v4.compatible_with
        assert "2.0" in schema_v4.compatible_with
        assert "3.0" in schema_v4.compatible_with


class TestMigrationMetadata:
    """Test migration metadata and risk levels"""

    def test_migration_risk_levels(self):
        """Verify migrations have appropriate risk levels"""
        registry = ArtifactSchemaRegistry()
        
        # All built-in migrations should be low risk
        for migration in registry.migrations.values():
            assert migration.risk_level in ["low", "medium", "high"]
            # Verify all default migrations are low risk
            if migration.from_version in ["1.0", "2.0", "3.0"]:
                assert migration.risk_level == "low"

    def test_migration_descriptions(self):
        """Verify migrations have descriptions"""
        registry = ArtifactSchemaRegistry()
        
        migration_1_2 = registry.get_migration("1.0", "2.0")
        assert migration_1_2.description is not None
        assert len(migration_1_2.description) > 0
        assert "learning" in migration_1_2.description.lower()

    def test_migration_rollback_capable(self):
        """Verify migrations are rollback capable"""
        registry = ArtifactSchemaRegistry()
        
        for migration in registry.migrations.values():
            assert migration.rollback_capable is True, \
                f"Migration {migration.from_version}→{migration.to_version} should be rollback capable"


class TestSchemaVersionEnum:
    """Test SchemaVersion enum"""

    def test_schema_version_enum_values(self):
        """Verify SchemaVersion enum has all versions"""
        assert SchemaVersion.V1.value == "1.0"
        assert SchemaVersion.V2.value == "2.0"
        assert SchemaVersion.V3.value == "3.0"
        assert SchemaVersion.V4.value == "4.0"
