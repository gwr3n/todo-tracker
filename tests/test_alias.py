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
    assert resolve_alias(a1, candidates) == u1
    
    # Case insensitive
    assert resolve_alias(a1.lower(), candidates) == u1
    assert resolve_alias(a1.upper(), candidates) == u1
    
    # Non-existent
    assert resolve_alias("Non-Existent", candidates) is None
