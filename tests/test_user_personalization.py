#!/usr/bin/env python3
"""
Test script for user personalization feature
Tests the new profile and user_instruction fields
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.models import UserModel
from app.services.user_service import user_service
from app.context.manager import ContextManager


async def test_user_personalization():
    """Test user personalization fields and context injection"""
    
    print("=" * 60)
    print("Testing User Personalization Feature")
    print("=" * 60)
    
    # Test 1: Check if user model has new fields
    print("\n[Test 1] Checking UserModel fields...")
    user_fields = [field for field in dir(UserModel) if not field.startswith('_')]
    has_profile = 'profile' in user_fields
    has_instruction = 'user_instruction' in user_fields
    
    print(f"  ✓ UserModel has 'profile' field: {has_profile}")
    print(f"  ✓ UserModel has 'user_instruction' field: {has_instruction}")
    
    if not (has_profile and has_instruction):
        print("  ✗ Missing required fields!")
        return False
    
    # Test 2: Test ContextManager with personalization
    print("\n[Test 2] Testing ContextManager with user personalization...")
    
    context_manager = ContextManager(
        system_prompt="You are CookHero, a cooking assistant."
    )
    
    test_profile = "我是素食主义者,喜欢清淡口味"
    test_instruction = "请用简洁的语言回答,多使用emoji"
    test_history = [
        {"role": "user", "content": "如何做宫保鸡丁?"},
        {"role": "assistant", "content": "这是一道经典川菜..."}
    ]
    
    messages = context_manager.build_llm_messages(
        history=test_history,
        compressed_count=0,
        compressed_summary=None,
        extra_system_prompt=None,
        user_profile=test_profile,
        user_instruction=test_instruction,
    )
    
    print(f"  ✓ Generated {len(messages)} messages")
    
    # Check if personalization is included
    has_personalization = False
    for msg in messages:
        if hasattr(msg, 'content') and '用户个人信息' in msg.content:
            has_personalization = True
            print(f"  ✓ User personalization found in context")
            break
    
    if not has_personalization:
        print("  ✗ User personalization not found in context!")
        return False
    
    # Test 3: Format personalization method
    print("\n[Test 3] Testing _format_user_personalization method...")
    
    formatted = context_manager._format_user_personalization(
        user_profile=test_profile,
        user_instruction=test_instruction
    )
    
    print(f"  ✓ Formatted personalization context ({len(formatted)} chars)")
    print("\n  Preview:")
    print("  " + "\n  ".join(formatted.split('\n')[:5]))
    
    # Test 4: Test with empty personalization
    print("\n[Test 4] Testing with empty personalization...")
    
    empty_formatted = context_manager._format_user_personalization(
        user_profile=None,
        user_instruction=None
    )
    
    if empty_formatted == "":
        print("  ✓ Empty personalization handled correctly")
    else:
        print("  ✗ Empty personalization should return empty string")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_user_personalization())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
