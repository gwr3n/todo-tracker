import pytest
from uuid import UUID
from src.alias import generate_alias, resolve_alias

def test_generate_alias_deterministic():
    u1 = UUID('3077bee6-3da3-4783-aff7-cbedfd5f5592')
    a1 = generate_alias(u1)
    
    # Same UUID should produce same alias
    assert generate_alias(u1) == a1
    
    # Check format
    parts = a1.split('-')
    assert len(parts) == 2
    assert len(parts[0]) > 0
    assert len(parts[1]) > 0

def test_generate_alias_different():
    u1 = UUID('3077bee6-3da3-4783-aff7-cbedfd5f5592')
    u2 = UUID('c4709ac5-4034-f7bb-27ac-93b3596223f9')
    
    a1 = generate_alias(u1)
    a2 = generate_alias(u2)
    
    assert a1 != a2

def test_resolve_alias():
    u1 = UUID('3077bee6-3da3-4783-aff7-cbedfd5f5592')
    u2 = UUID('c4709ac5-4034-f7bb-27ac-93b3596223f9')
    
    a1 = generate_alias(u1)
    candidates = [u1, u2]
    
    # Exact match
    result = resolve_alias(a1, candidates)
    assert result is not None
    assert result[0] == u1
    assert result[1] is None  # No version
    
    # Case insensitive
    result = resolve_alias(a1.lower(), candidates)
    assert result[0] == u1
    
    result = resolve_alias(a1.upper(), candidates)
    assert result[0] == u1
    
    # Non-existent
    assert resolve_alias("Non-Existent", candidates) is None

def test_resolve_alias_with_version():
    u1 = UUID('3077bee6-3da3-4783-aff7-cbedfd5f5592')
    a1 = generate_alias(u1)
    candidates = [u1]
    
    # Version 1
    result = resolve_alias(f"{a1}-1", candidates)
    assert result is not None
    assert result[0] == u1
    assert result[1] == 1
    
    # Version 5
    result = resolve_alias(f"{a1}-5", candidates)
    assert result[0] == u1
    assert result[1] == 5
    
    # Case insensitive with version
    result = resolve_alias(f"{a1.lower()}-3", candidates)
    assert result[0] == u1
    assert result[1] == 3
