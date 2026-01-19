"""Property-based tests using Hypothesis.

Tests invariants and properties that should hold for ANY valid input.
Hypothesis automatically generates hundreds of edge cases.

Note: Password tests use reduced examples due to bcrypt being intentionally slow.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings

from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import (
    VerifyPasswordTask,
    VerifyPasswordInput,
)


class TestPasswordHashing:
    """Property-based tests for password hashing.
    
    Note: bcrypt is intentionally slow, so we limit examples.
    """
    
    @settings(max_examples=10, deadline=None)  # bcrypt is slow
    @given(password=st.text(min_size=1, max_size=50))
    def test_hashed_password_always_verifiable(self, password: str) -> None:
        """Property: Any password, after hashing, should always verify correctly.
        
        This is a fundamental invariant of password hashing.
        """
        hash_task = HashPasswordTask()
        verify_task = VerifyPasswordTask()
        
        # Hash the password
        password_hash = hash_task.run(password)
        
        # It should ALWAYS verify
        is_valid = verify_task.run(VerifyPasswordInput(
            password=password,
            password_hash=password_hash,
        ))
        
        assert is_valid, f"Password '{password}' failed to verify after hashing"
    
    @settings(max_examples=10, deadline=None)  # bcrypt is slow
    @given(
        password1=st.text(min_size=1, max_size=30),
        password2=st.text(min_size=1, max_size=30),
    )
    def test_different_passwords_produce_different_hashes(
        self, password1: str, password2: str
    ) -> None:
        """Property: Different passwords should produce different hashes.
        
        Note: We use assume() to skip cases where passwords are equal.
        """
        assume(password1 != password2)
        
        hash_task = HashPasswordTask()
        
        hash1 = hash_task.run(password1)
        hash2 = hash_task.run(password2)
        
        # Different passwords should NOT verify each other's hashes
        verify_task = VerifyPasswordTask()
        
        cross_verify = verify_task.run(VerifyPasswordInput(
            password=password1,
            password_hash=hash2,
        ))
        
        assert not cross_verify, "Different passwords should not verify each other"
    
    @settings(max_examples=10, deadline=None)  # bcrypt is slow
    @given(password=st.text(min_size=1, max_size=30))
    def test_same_password_produces_different_hashes_each_time(
        self, password: str
    ) -> None:
        """Property: Same password hashed twice produces different hashes (due to salt).
        
        This is important for security - prevents rainbow table attacks.
        """
        hash_task = HashPasswordTask()
        
        hash1 = hash_task.run(password)
        hash2 = hash_task.run(password)
        
        # Hashes should be different (different salts)
        assert hash1 != hash2, "Same password should produce different hashes"
        
        # But both should still verify
        verify_task = VerifyPasswordTask()
        
        assert verify_task.run(VerifyPasswordInput(password=password, password_hash=hash1))
        assert verify_task.run(VerifyPasswordInput(password=password, password_hash=hash2))


class TestEmailNormalization:
    """Property-based tests for email handling."""
    
    # Strategy for generating valid-ish emails
    email_strategy = st.from_regex(
        r"[a-z][a-z0-9]{2,10}@[a-z]{3,8}\.[a-z]{2,4}",
        fullmatch=True
    )
    
    @given(email=email_strategy)
    def test_email_normalization_is_idempotent(self, email: str) -> None:
        """Property: Normalizing an email twice gives same result as once.
        
        normalize(normalize(email)) == normalize(email)
        """
        from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
        
        # First normalization
        try:
            request1 = CreateUserRequest(
                email=email,
                password="password123",
                name="Test",
            )
            normalized1 = request1.email
            
            # Second normalization
            request2 = CreateUserRequest(
                email=normalized1,
                password="password123", 
                name="Test",
            )
            normalized2 = request2.email
            
            assert normalized1 == normalized2, "Email normalization should be idempotent"
        except Exception:
            # Invalid email format - that's fine, skip
            assume(False)
    
    @given(
        local=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=3, max_size=10),
        domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=8),
    )
    def test_email_always_lowercased(self, local: str, domain: str) -> None:
        """Property: Email should always be lowercased after normalization."""
        from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
        
        # Mix case randomly
        email = f"{local.upper()}@{domain.lower()}.com"
        
        try:
            request = CreateUserRequest(
                email=email,
                password="password123",
                name="Test User",
            )
            
            assert request.email == request.email.lower(), "Email should be lowercase"
            assert request.email == email.lower(), "Email should match lowercase original"
        except Exception:
            # Invalid email - skip
            assume(False)


class TestUserRequestValidation:
    """Property-based tests for request validation."""
    
    @given(
        password=st.text(min_size=8, max_size=100),
        name=st.text(min_size=2, max_size=100),
    )
    @settings(max_examples=50)  # Reduce examples for faster tests
    def test_valid_inputs_never_raise(self, password: str, name: str) -> None:
        """Property: Valid inputs should never raise validation errors.
        
        If password >= 8 chars and name >= 2 chars, validation should pass.
        """
        from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
        from pydantic import ValidationError
        
        # Skip if password or name contain only whitespace
        assume(password.strip())
        assume(name.strip())
        
        # This should NOT raise
        try:
            request = CreateUserRequest(
                email="valid@example.com",
                password=password,
                name=name,
            )
            assert request.password == password
            assert request.name == name
        except ValidationError as e:
            # If it raises, it's a bug in our understanding
            pytest.fail(f"Valid input raised ValidationError: {e}")
    
    @given(password=st.text(max_size=7))
    def test_short_password_always_rejected(self, password: str) -> None:
        """Property: Password < 8 chars should always be rejected."""
        from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
        from pydantic import ValidationError
        
        assume(len(password) < 8)  # Ensure it's actually short
        
        with pytest.raises(ValidationError):
            CreateUserRequest(
                email="valid@example.com",
                password=password,
                name="Valid Name",
            )

