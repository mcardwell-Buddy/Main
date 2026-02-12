"""
Artifact Schema Versioning System (Phase 4a)

Manages artifact schema evolution and backward compatibility:
- Schema version tracking
- Schema migration framework
- Validation for schema enforcement
- Migration path discovery
- Backward compatibility support

Non-blocking: schema validation failures logged but don't affect execution
Feature-flagged: SCHEMA_VERSIONING_ENABLED controls validation
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class SchemaVersion(Enum):
    """Artifact schema versions."""
    V1 = "1.0"  # Initial schema (Phase 1)
    V2 = "2.0"  # Learning insights added (Phase 2)
    V3 = "3.0"  # Relationship metadata (Phase 3)
    V4 = "4.0"  # Cost tracking (Phase 4)


@dataclass
class SchemaMetadata:
    """Metadata about a schema version."""
    version: str
    released_at: str  # ISO8601 datetime
    description: str
    breaking_changes: List[str]
    deprecated_fields: List[str]
    new_fields: List[str]
    migration_required: bool
    compatible_with: List[str]  # Earlier versions this is compatible with


@dataclass
class SchemaMigration:
    """Schema migration definition."""
    from_version: str
    to_version: str
    migrator: Callable
    risk_level: str  # "low", "medium", "high"
    rollback_capable: bool
    description: str


class ArtifactSchemaRegistry:
    """
    Central registry for artifact schema definitions and migrations.
    
    Manages schema versions, validation functions, and migration paths.
    """

    def __init__(self):
        """Initialize schema registry."""
        self.schemas: Dict[str, SchemaMetadata] = {}
        self.migrations: Dict[Tuple[str, str], SchemaMigration] = {}
        self.validators: Dict[str, Callable] = {}
        self._initialize_builtin_schemas()
        self._initialize_validators()
        logger.info("[SCHEMA] Registry initialized")

    def _initialize_validators(self):
        """Register built-in validators."""
        self.register_validator("1.0", ArtifactSchemaValidator.validate_v1_0)
        self.register_validator("2.0", ArtifactSchemaValidator.validate_v2_0)
        self.register_validator("3.0", ArtifactSchemaValidator.validate_v3_0)
        self.register_validator("4.0", ArtifactSchemaValidator.validate_v4_0)

    def _initialize_builtin_schemas(self):
        """Initialize built-in schema definitions."""
        # Schema v1.0: Initial artifact schema (Phase 1)
        self.register_schema(
            SchemaMetadata(
                version="1.0",
                released_at="2026-01-01T00:00:00Z",
                description="Initial artifact schema with basic metadata",
                breaking_changes=[],
                deprecated_fields=[],
                new_fields=["artifact_id", "artifact_type", "status", "created_at", "metrics"],
                migration_required=False,
                compatible_with=[]
            )
        )

        # Schema v2.0: Learning signals (Phase 2)
        self.register_schema(
            SchemaMetadata(
                version="2.0",
                released_at="2026-02-01T00:00:00Z",
                description="Added learning insights and signal processing",
                breaking_changes=[],
                deprecated_fields=[],
                new_fields=["learning_insights", "confidence_score"],
                migration_required=False,
                compatible_with=["1.0"]
            )
        )

        # Schema v3.0: Relationship metadata (Phase 3)
        self.register_schema(
            SchemaMetadata(
                version="3.0",
                released_at="2026-02-12T00:00:00Z",
                description="Added artifact relationships and graph metadata",
                breaking_changes=[],
                deprecated_fields=[],
                new_fields=["relationships", "relationship_metadata"],
                migration_required=False,
                compatible_with=["1.0", "2.0"]
            )
        )

        # Schema v4.0: Cost tracking (Phase 4)
        self.register_schema(
            SchemaMetadata(
                version="4.0",
                released_at="2026-02-12T00:00:00Z",
                description="Added cost tracking and reconciliation",
                breaking_changes=[],
                deprecated_fields=[],
                new_fields=["cost_estimate", "cost_actual", "cost_variance"],
                migration_required=False,
                compatible_with=["1.0", "2.0", "3.0"]
            )
        )

        # Register migrations
        self._register_builtin_migrations()

    def _register_builtin_migrations(self):
        """Register built-in migration paths."""
        # 1.0 → 2.0: Add learning fields with defaults
        self.register_migration(
            SchemaMigration(
                from_version="1.0",
                to_version="2.0",
                migrator=self._migrate_1_0_to_2_0,
                risk_level="low",
                rollback_capable=True,
                description="Add learning insights and confidence scores"
            )
        )

        # 2.0 → 3.0: Add relationship fields
        self.register_migration(
            SchemaMigration(
                from_version="2.0",
                to_version="3.0",
                migrator=self._migrate_2_0_to_3_0,
                risk_level="low",
                rollback_capable=True,
                description="Add artifact relationships and graph metadata"
            )
        )

        # 3.0 → 4.0: Add cost tracking
        self.register_migration(
            SchemaMigration(
                from_version="3.0",
                to_version="4.0",
                migrator=self._migrate_3_0_to_4_0,
                risk_level="low",
                rollback_capable=True,
                description="Add cost tracking and reconciliation fields"
            )
        )

    def register_schema(self, schema: SchemaMetadata):
        """Register a schema version."""
        self.schemas[schema.version] = schema
        logger.debug(f"[SCHEMA] Registered schema {schema.version}: {schema.description}")

    def register_migration(self, migration: SchemaMigration):
        """Register a migration path."""
        key = (migration.from_version, migration.to_version)
        self.migrations[key] = migration
        logger.debug(
            f"[SCHEMA] Registered migration {migration.from_version} → {migration.to_version} "
            f"(risk: {migration.risk_level})"
        )

    def register_validator(self, version: str, validator: Callable):
        """Register a validation function for a schema version."""
        self.validators[version] = validator
        logger.debug(f"[SCHEMA] Registered validator for schema {version}")

    def get_schema(self, version: str) -> Optional[SchemaMetadata]:
        """Get schema metadata by version."""
        return self.schemas.get(version)

    def get_migration(self, from_version: str, to_version: str) -> Optional[SchemaMigration]:
        """Get migration path between two versions."""
        return self.migrations.get((from_version, to_version))

    def get_migration_path(self, from_version: str, to_version: str) -> List[SchemaMigration]:
        """
        Find migration path between two versions using BFS.
        
        Args:
            from_version: Starting schema version
            to_version: Target schema version
            
        Returns:
            List of migrations to apply in order, or empty list if no path exists
        """
        if from_version == to_version:
            return []

        # BFS to find shortest migration path
        queue = [(from_version, [from_version])]
        visited = {from_version}
        
        while queue:
            current, path = queue.pop(0)
            
            if current == to_version:
                # Build migration list
                migrations = []
                for i in range(len(path) - 1):
                    migration = self.get_migration(path[i], path[i + 1])
                    if migration:
                        migrations.append(migration)
                    else:
                        logger.warning(f"[SCHEMA] No migration found: {path[i]} → {path[i + 1]}")
                        return []
                return migrations
            
            # Find next versions
            for (src, dst), migration in self.migrations.items():
                if src == current and dst not in visited:
                    visited.add(dst)
                    queue.append((dst, path + [dst]))
        
        logger.warning(f"[SCHEMA] No migration path found: {from_version} → {to_version}")
        return []

    def validate_artifact(self, artifact: Dict[str, Any], schema_version: str) -> Tuple[bool, List[str]]:
        """
        Validate artifact against schema version.
        
        Args:
            artifact: Artifact data to validate
            schema_version: Target schema version
            
        Returns:
            (is_valid, error_list) tuple
        """
        validator = self.validators.get(schema_version)
        if not validator:
            logger.debug(f"[SCHEMA] No validator registered for version {schema_version}")
            return True, []
        
        try:
            errors = validator(artifact)
            is_valid = len(errors) == 0
            return is_valid, errors
        except Exception as e:
            logger.warning(f"[SCHEMA] Validation error for {schema_version}: {e}")
            return False, [str(e)]

    def migrate_artifact(self, artifact: Dict[str, Any], from_version: str, to_version: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Migrate artifact from one schema version to another.
        
        Args:
            artifact: Artifact data
            from_version: Current schema version
            to_version: Target schema version
            
        Returns:
            (success, migrated_artifact, message) tuple
        """
        if from_version == to_version:
            return True, artifact, "No migration needed"

        migrations = self.get_migration_path(from_version, to_version)
        if not migrations:
            logger.error(f"[SCHEMA] Cannot migrate {from_version} → {to_version}")
            return False, artifact, f"No migration path found"

        current = artifact.copy()
        for migration in migrations:
            try:
                current = migration.migrator(current)
                logger.debug(f"[SCHEMA] Migrated {migration.from_version} → {migration.to_version}")
            except Exception as e:
                logger.error(f"[SCHEMA] Migration failed {migration.from_version} → {migration.to_version}: {e}")
                return False, artifact, f"Migration failed: {e}"

        return True, current, f"Successfully migrated to {to_version}"

    # Built-in migrators
    @staticmethod
    def _migrate_1_0_to_2_0(artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate 1.0 → 2.0: Add learning fields."""
        migrated = artifact.copy()
        if "learning_insights" not in migrated:
            migrated["learning_insights"] = []
        if "confidence_score" not in migrated:
            # Infer confidence from metrics if available
            metrics = migrated.get("metrics", {})
            migrated["confidence_score"] = metrics.get("confidence_score", 0.5)
        migrated["schema_version"] = "2.0"
        return migrated

    @staticmethod
    def _migrate_2_0_to_3_0(artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate 2.0 → 3.0: Add relationship fields."""
        migrated = artifact.copy()
        if "relationships" not in migrated:
            migrated["relationships"] = []
        if "relationship_metadata" not in migrated:
            migrated["relationship_metadata"] = {}
        migrated["schema_version"] = "3.0"
        return migrated

    @staticmethod
    def _migrate_3_0_to_4_0(artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate 3.0 → 4.0: Add cost tracking fields."""
        migrated = artifact.copy()
        if "cost_estimate" not in migrated:
            migrated["cost_estimate"] = 0.0
        if "cost_actual" not in migrated:
            migrated["cost_actual"] = 0.0
        if "cost_variance" not in migrated:
            migrated["cost_variance"] = 0.0
        migrated["schema_version"] = "4.0"
        return migrated


class ArtifactSchemaValidator:
    """Validates artifacts against schema definitions."""

    @staticmethod
    def validate_v1_0(artifact: Dict[str, Any]) -> List[str]:
        """Validate artifact against schema 1.0."""
        errors = []
        required = ["artifact_id", "artifact_type", "status", "created_at"]
        for field in required:
            if field not in artifact:
                errors.append(f"Missing required field: {field}")
        return errors

    @staticmethod
    def validate_v2_0(artifact: Dict[str, Any]) -> List[str]:
        """Validate artifact against schema 2.0."""
        errors = ArtifactSchemaValidator.validate_v1_0(artifact)
        
        # Check for learning fields
        if "confidence_score" in artifact:
            score = artifact["confidence_score"]
            if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                errors.append("confidence_score must be between 0.0 and 1.0")
        
        return errors

    @staticmethod
    def validate_v3_0(artifact: Dict[str, Any]) -> List[str]:
        """Validate artifact against schema 3.0."""
        errors = ArtifactSchemaValidator.validate_v2_0(artifact)
        
        # Check relationships format
        if "relationships" in artifact:
            rel = artifact["relationships"]
            if not isinstance(rel, list):
                errors.append("relationships must be a list")
        
        return errors

    @staticmethod
    def validate_v4_0(artifact: Dict[str, Any]) -> List[str]:
        """Validate artifact against schema 4.0."""
        errors = ArtifactSchemaValidator.validate_v3_0(artifact)
        
        # Check cost fields
        for field in ["cost_estimate", "cost_actual", "cost_variance"]:
            if field in artifact:
                value = artifact[field]
                if not isinstance(value, (int, float)) or value < 0:
                    errors.append(f"{field} must be a non-negative number")
        
        return errors


# Global singleton
_schema_registry: Optional[ArtifactSchemaRegistry] = None


def get_schema_registry() -> ArtifactSchemaRegistry:
    """Get or create global schema registry singleton."""
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = ArtifactSchemaRegistry()
        # Validators are now registered in __init__
    
    return _schema_registry
