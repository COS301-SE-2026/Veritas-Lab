from app.auth.auth import hashPassword,verifyPassword

def testHashPasswordReturnsString():
    hashedPassword =hashPassword("StrongP@ssword1234567")
    assert isinstance(hashedPassword, str)

def testHashPasswordDoesNotReturnPlainPassword():
    password = "StrongP@ssword1234567"
    hashedPassword = hashPassword(password)
    assert hashedPassword!= password

def testHashPasswordProducesDifferentHashes():
    password = "StrongP@ssword1234567"
    hashedPassword1= hashPassword(password)
    hashedPassword2 = hashPassword(password)
    assert hashedPassword1 != hashedPassword2

def testVerifyPasswordReturnsTrueForCorrectPassword():
    password= "StrongP@ssword1234567"
    hashedPassword = hashPassword(password)
    assert verifyPassword(password, hashedPassword) == True

def testVerifyPasswordReturnsFalseForIncorrectPassword():
    password = "StrongP@ssword1234567"
    wrongPassword ="WrongP@ssword1234567890"
    hashedPassword = hashPassword(password)
    assert verifyPassword(wrongPassword, hashedPassword) == False