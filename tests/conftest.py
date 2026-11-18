import os
import tempfile

# Set before any app module is imported, so tests use a throwaway database
# and never fall back to a default secret or default admin account.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-tests-only-0123456789"
os.environ["ADMIN_USERNAME"] = "test-admin"
os.environ["ADMIN_PASSWORD"] = "test-password"
