import re

# 1. test_user_service.py
with open("tests/unit/test_user_service.py", "r") as f:
    content = f.read()

# Add imports at the top
content = content.replace(
    "import pytest\nfrom unittest.mock import AsyncMock, MagicMock, patch",
    "import pytest\nimport uuid\nfrom fastapi import HTTPException\nfrom unittest.mock import AsyncMock, MagicMock, patch"
)

# Remove inline imports
content = re.sub(r' +from fastapi import HTTPException\n', '', content)
content = re.sub(r' +import uuid\n', '', content)

with open("tests/unit/test_user_service.py", "w") as f:
    f.write(content)


# 2. test_auth.py
with open("tests/integration/test_auth.py", "r") as f:
    auth_lines = f.readlines()

new_auth = []
in_class = False
for line in auth_lines:
    if line.startswith("# Signup"):
        new_auth.append(line)
        new_auth.append("# """ + "-"*75 + """\n\nclass TestSignup:\n")
        in_class = True
        continue
    elif line.startswith("# Login"):
        new_auth.append(line)
        new_auth.append("# """ + "-"*75 + """\n\nclass TestLogin:\n")
        in_class = True
        continue
    elif line.startswith("# Signup token is a valid JWT"):
        new_auth.append(line)
        new_auth.append("# """ + "-"*75 + """\n\nclass TestJWT:\n")
        in_class = True
        continue
    elif line.startswith("# """ + "-"*75):
        if not in_class:
            new_auth.append(line)
        continue
        
    if line.startswith("async def test_"):
        line = line.replace("client)", "self, client)")
        new_auth.append("    " + line)
    elif in_class and line.strip() and not line.startswith("#") and not line.startswith("SIGNUP_URL") and not line.startswith("LOGIN_URL") and not line.startswith("VALID_"):
        if not line.startswith("import "):
            new_auth.append("    " + line)
        else:
            new_auth.append("    " + line)
    elif in_class and not line.strip():
        new_auth.append(line)
    else:
        new_auth.append(line)

with open("tests/integration/test_auth.py", "w") as f:
    f.writelines(new_auth)

# 3. test_db.py
with open("tests/integration/test_db.py", "r") as f:
    db_content = f.read()

db_content = db_content.replace(
    "@pytest.mark.asyncio\nasync def test_database_connection():",
    "class TestDatabase:\n    @pytest.mark.asyncio\n    async def test_database_connection(self):"
)
db_content = db_content.replace(
    '    """Verify that the engine can open',
    '        """Verify that the engine can open'
)
db_content = db_content.replace(
    "    async with engine.connect() as conn:",
    "        async with engine.connect() as conn:"
)
db_content = db_content.replace(
    "        result = await conn.execute(text(\"SELECT 1\"))",
    "            result = await conn.execute(text(\"SELECT 1\"))"
)
db_content = db_content.replace(
    "        row = result.scalar()",
    "            row = result.scalar()"
)
db_content = db_content.replace(
    "    assert row == 1",
    "        assert row == 1"
)

with open("tests/integration/test_db.py", "w") as f:
    f.write(db_content)

print("Done refactoring.")
