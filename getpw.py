def encryptcaesar(text, s):
    result = ""

    # traverse text
    for i in range(len(text)):
        char = text[i]

        # Encrypt uppercase characters
        if char.isupper():
            result += chr((ord(char) + s - 65) % 26 + 65)

        # Encrypt lowercase characters
        else:
            result += chr((ord(char) + s - 97) % 26 + 97)

    return result


def getencryptedpassword():
    return "example"
    # this is so people can't see your password at first glance


def getsudopassword(process):
    process.communicate(bytes(str("<PASSWORD HERE>"), encoding="utf8"))

