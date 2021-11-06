import app.auth as auth


def test_password_flow():
    """Test password hashing and verifying with some different passwords."""
    passwords = ["hello", "world", "A" * 1000, "", "ӁӁӁ", "ٸ", "៼"]
    for password in passwords:
        correct, _ = auth.verify_update_password(
            password,
            auth.hash_password(password),
        )
        assert correct
