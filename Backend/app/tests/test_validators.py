from app.api.main import validateEmail
from app.api.main import validatePassword

def testValidEmail():
    assert validateEmail("u12345678@tuks.co.za") is True

def testInvalidEmail():
    assert validateEmail("hello world") is False

def testEmptyEmail():
    assert validateEmail("") is False

def testEmailTrimming():
    assert validateEmail("  u12345678@tuks.co.za  ") is True

def testPasswordMissingSpecial():
    assert validatePassword("ThisIsAStrongPassword123") is False

def testPasswordLength():
    assert validatePassword("Strong1@") is False

def testPasswordNumber():
    assert validatePassword("@QWertyuipsjdnasndoajd&&sa1235678991") is False

def testPasswordUpperCase():
    assert validatePassword("qwertyuiopasddf123455!@#$sasd") is False

def testPasswordLowerCase():
    assert validatePassword("QUYGYUGUIHUIGYUGUIHUIHI12345321!##@#$") is False

def testPasswordMissing():
    assert validatePassword("") is False

def testInvalidPassword():
    assert validatePassword("ThisIsAStrongPassword123@@") is True

