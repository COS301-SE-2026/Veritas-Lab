from app.auth.auth import hash_password,verify_password

def test_hash_password_returns_string():
    hashed_password = hash_password("StrongP@ssword1234567")
    assert isinstance(hashed_password, str)

def test_hash_password_does_not_return_plain_password():
    password = "StrongP@ssword1234567"
    hashed_password = hash_password(password)
    assert hashed_password!= password

def test_hash_password_produces_different_hashes():
    password = "StrongP@ssword1234567"
    hashed_password1 = hash_password(password)
    hashed_password2 = hash_password(password)
    assert hashed_password1 != hashed_password2

def test_verify_password_returns_true_for_correct_password():
    password = "StrongP@ssword1234567"
    hashed_password = hash_password(password)
    assert verify_password(password, hashed_password) == True

def test_verify_password_returns_false_for_incorrect_pssword():
    password = "StrongP@ssword1234567"
    wrong_password ="WrongP@ssword1234567890"
    hashed_password = hash_password(password)
    assert verify_password(wrong_password, hashed_password) == False