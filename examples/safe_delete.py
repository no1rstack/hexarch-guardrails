"""
Example: Safe File Operations
Shows how to protect destructive operations like delete
"""
from hexarch_guardrails import Guardian
import os

guardian = Guardian()


@guardian.check("safe_delete", context={"resource_type": "file"})
def delete_file(file_path: str) -> bool:
    """
    Delete a file, but require confirmation first
    """
    os.remove(file_path)
    return True


@guardian.check("safe_delete", context={"resource_type": "directory"})
def delete_directory(dir_path: str) -> bool:
    """
    Delete a directory, but require confirmation first
    """
    import shutil
    shutil.rmtree(dir_path)
    return True


@guardian.check("safe_delete", context={"resource_type": "database", "table": "users"})
def truncate_database_table(db, table: str) -> bool:
    """
    Truncate a database table with extra safeguards
    """
    db.execute(f"TRUNCATE TABLE {table}")
    return True


if __name__ == "__main__":
    print("Hexarch Guardrails - Safe File Operations")
    print("=" * 50)
    print(f"✓ Guardian initialized")
    print(f"✓ Available policies: {guardian.list_policies()}")
    print()
    print("To use:")
    print("  from examples.safe_delete import delete_file")
    print("  delete_file('/path/to/file.txt')")
    print()
    print("The guardian will require confirmation before")
    print("allowing destructive operations.")
