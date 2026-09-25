from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


class PasswordHandler:
    def hash_plain_pwd(self, pln_pwd: str) -> str:
        if not pln_pwd:
            raise ValueError("Plain Password wasn't provided...")
        return ph.hash(pln_pwd)

    def verify_pwd(self, pln_pwd: str, stored_hash: str) -> bool:
        if not pln_pwd or not stored_hash:
            raise ValueError("Required parameters missing for verification.")
        try:
            return ph.verify(stored_hash, pln_pwd)
        except VerifyMismatchError:
            return False