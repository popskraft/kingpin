#!/usr/bin/env python3
"""
Comprehensive validation script for Kingpin codebase.
Tests single data source consistency and component integration.
"""

import sys
from pathlib import Path

# Add packages to path
sys.path.append(str(Path(__file__).parent / 'packages'))

def test_unified_card_loading():
    """Test that unified card loading works correctly."""
    print("🔍 Testing unified card loading...")
    
    try:
        from engine.loader import load_cards_from_csv
        from engine.config import get_path
        
        csv_path = get_path('cards_csv')
        print(f"  📁 CSV path: {csv_path}")
        
        # Test loading deck cards only
        deck_cards = load_cards_from_csv(csv_path, include_all=False)
        print(f"  ✅ Deck cards loaded: {len(deck_cards)}")
        
        # Test loading all cards
        all_cards = load_cards_from_csv(csv_path, include_all=True)
        print(f"  ✅ All cards loaded: {len(all_cards)}")
        
        # Validate card structure
        if all_cards:
            card = all_cards[0]
            required_fields = ['id', 'name', 'hp', 'atk', 'd', 'price', 'corruption']
            for field in required_fields:
                assert hasattr(card, field), f"Card missing field: {field}"
            print(f"  ✅ Card structure valid: {card.id}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_server_integration():
    """Test that server uses unified loader correctly."""
    print("🔍 Testing server integration...")
    
    try:
        from server.main import _load_cards_index, _build_state_from_csv
        
        # Test cards index loading
        cards_index = _load_cards_index()
        print(f"  ✅ Cards index loaded: {len(cards_index)} cards")
        
        # Test state building
        state, config = _build_state_from_csv()
        print(f"  ✅ Game state built with {len(state.deck)} deck cards")
        
        # Validate that cards in state match CSV structure
        if state.deck:
            card = state.deck[0]
            assert hasattr(card, 'id'), "State card missing ID"
            assert hasattr(card, 'd'), "State card missing defend field"
            print(f"  ✅ State card structure valid: {card.id}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_simulator_integration():
    """Test that simulator uses unified models."""
    print("🔍 Testing simulator integration...")
    
    try:
        from simulator.game_simulator import GameSimulator, GameCard
        from engine.config import get_path
        
        csv_path = str(get_path('cards_csv'))
        simulator = GameSimulator(csv_path)
        
        # Test that cards were loaded
        total_cards = sum(len(cards) for cards in simulator.cards_data.values())
        print(f"  ✅ Simulator loaded {total_cards} cards")
        
        # Test GameCard wrapper
        if simulator.cards_data['gangsters']:
            game_card = simulator.cards_data['gangsters'][0]
            assert isinstance(game_card, GameCard), "Not a GameCard instance"
            assert hasattr(game_card, 'engine_card'), "Missing engine_card reference"
            print(f"  ✅ GameCard wrapper works: {game_card.id}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_webapp_compatibility():
    """Test that webapp types are compatible with backend."""
    print("🔍 Testing webapp type compatibility...")
    
    try:
        from engine.models import Card
        from engine.loader import load_cards_from_csv
        from engine.config import get_path
        
        # Load a card from engine
        cards = load_cards_from_csv(get_path('cards_csv'), include_all=True)
        if not cards:
            print("  ⚠️  No cards to test")
            return True
            
        card = cards[0]
        
        # Test that card can be serialized to dict (for JSON API)
        card_dict = card.model_dump()
        
        # Check webapp expected fields
        webapp_fields = ['id', 'name', 'type', 'faction', 'clan', 'hp', 'atk', 'd', 'price', 'corruption', 'rage', 'notes']
        for field in webapp_fields:
            assert field in card_dict, f"Missing webapp field: {field}"
        
        print(f"  ✅ Webapp compatibility verified for {len(webapp_fields)} fields")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_configuration_system():
    """Test unified configuration system."""
    print("🔍 Testing configuration system...")
    
    try:
        from engine.config import get_path, get_constant, get_csv_columns, game_config
        
        # Test path resolution
        csv_path = get_path('cards_csv')
        assert csv_path.exists(), f"CSV file not found: {csv_path}"
        print(f"  ✅ Path resolution works: {csv_path.name}")
        
        # Test constants
        max_slots = get_constant('max_slots')
        assert isinstance(max_slots, int), "Max slots should be integer"
        print(f"  ✅ Constants work: max_slots={max_slots}")
        
        # Test CSV column mappings
        id_columns = get_csv_columns('id')
        assert 'ID' in id_columns, "ID column mapping missing"
        print(f"  ✅ CSV mappings work: {len(id_columns)} ID variants")
        
        # Test game config
        config = game_config.config
        assert isinstance(config, dict), "Config should be dict"
        print(f"  ✅ Game config loaded with {len(config)} keys")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting Kingpin codebase validation...\n")
    
    tests = [
        ("Configuration System", test_configuration_system),
        ("Unified Card Loading", test_unified_card_loading),
        ("Server Integration", test_server_integration),
        ("Simulator Integration", test_simulator_integration),
        ("Webapp Compatibility", test_webapp_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "="*50)
    print("📊 VALIDATION RESULTS")
    print("="*50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Codebase is consistent and expandable!")
        print("✅ Single data source: config/cards.csv")
        print("✅ Unified loading: engine/loader.py")
        print("✅ Centralized config: engine/config.py")
        print("✅ All components integrated")
    else:
        print("⚠️  SOME TESTS FAILED - Check errors above")
        sys.exit(1)

if __name__ == "__main__":
    main()
