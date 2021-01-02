import app.main as main
import app.cryptography as cryptography


def test_password_hashing():
    """Test password hashing and verifying with diverse passwords."""
    passwords = ['hello', 'world', 'A'*1000, '', 'Ӂ', 'ٸ', '៼']
    password_manager = main.account_manager.password_manager
    for password in passwords:
        password_hash = password_manager.hash_password(password)
        assert password_manager.verify_password(password, password_hash)

def test_access_token_generation(admin_name):
    """Test JWT access token generation and decoding procedure."""
    access_token = main.token_manager.generate(admin_name)
    assert admin_name == main.token_manager.decode(access_token)
