"""Replace requires_superuser with edit_requires_superuser and view_requires_superuser

Revision ID: replace_requires_superuser
Revises: d6bac3d18831
Create Date: 2023-07-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'replace_requires_superuser'
down_revision = 'd6bac3d18831'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table for attributes with the new columns
    op.execute("""
    CREATE TABLE attributes_new (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        schema JSON NOT NULL,
        edit_requires_superuser BOOLEAN NOT NULL DEFAULT '0',
        view_requires_superuser BOOLEAN NOT NULL DEFAULT '0',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    )
    """)
    
    # Copy data from old table to new table
    op.execute("""
    INSERT INTO attributes_new (id, schema, edit_requires_superuser, created_at, updated_at)
    SELECT id, schema, requires_superuser, created_at, updated_at FROM attributes
    """)
    
    # Drop old table and rename new table
    op.execute("DROP TABLE attributes")
    op.execute("ALTER TABLE attributes_new RENAME TO attributes")
    
    # Create a new table for tags with the new columns
    op.execute("""
    CREATE TABLE tags_new (
        code VARCHAR NOT NULL PRIMARY KEY,
        title VARCHAR NOT NULL,
        description VARCHAR,
        edit_requires_superuser BOOLEAN NOT NULL DEFAULT '0',
        view_requires_superuser BOOLEAN NOT NULL DEFAULT '0',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    )
    """)
    
    # Copy data from old table to new table
    op.execute("""
    INSERT INTO tags_new (code, title, description, edit_requires_superuser, created_at, updated_at)
    SELECT code, title, description, requires_superuser, created_at, updated_at FROM tags
    """)
    
    # Drop old table and rename new table
    op.execute("DROP TABLE tags")
    op.execute("ALTER TABLE tags_new RENAME TO tags")


def downgrade():
    # Create a new table for attributes with the old column
    op.execute("""
    CREATE TABLE attributes_old (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        schema JSON NOT NULL,
        requires_superuser BOOLEAN NOT NULL DEFAULT '0',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    )
    """)
    
    # Copy data from new table to old table
    op.execute("""
    INSERT INTO attributes_old (id, schema, requires_superuser, created_at, updated_at)
    SELECT id, schema, edit_requires_superuser, created_at, updated_at FROM attributes
    """)
    
    # Drop new table and rename old table
    op.execute("DROP TABLE attributes")
    op.execute("ALTER TABLE attributes_old RENAME TO attributes")
    
    # Create a new table for tags with the old column
    op.execute("""
    CREATE TABLE tags_old (
        code VARCHAR NOT NULL PRIMARY KEY,
        title VARCHAR NOT NULL,
        description VARCHAR,
        requires_superuser BOOLEAN NOT NULL DEFAULT '0',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    )
    """)
    
    # Copy data from new table to old table
    op.execute("""
    INSERT INTO tags_old (code, title, description, requires_superuser, created_at, updated_at)
    SELECT code, title, description, edit_requires_superuser, created_at, updated_at FROM tags
    """)
    
    # Drop new table and rename old table
    op.execute("DROP TABLE tags")
    op.execute("ALTER TABLE tags_old RENAME TO tags")