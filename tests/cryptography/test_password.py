import app.cryptography.password as pw


def test_password_hashing():
    """Test password hashing and verifying with some different passwords."""
    passwords = ['hello', 'world', 'A'*1000, '', 'ӁӁӁ', 'ٸ', '៼']
    for password in passwords:
        assert pw.verify(password, pw.hash(password))
