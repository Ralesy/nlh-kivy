"""
Tests for hybrid controls system.
"""

import unittest
from core.hybrid_controls import HybridControlManager


class TestHybridControls(unittest.TestCase):
    """Test cases for hybrid controls."""

    def setUp(self):
        self.controls = HybridControlManager()

    def test_keyboard_movement(self):
        """Test WASD keyboard movement."""
        # Test W key
        self.controls.handle_keyboard('w', True)
        self.assertEqual(self.controls.get_movement_vector((0, 0)), [0, 1])
        self.controls.handle_keyboard('w', False)

        # Test S key
        self.controls.handle_keyboard('s', True)
        self.assertEqual(self.controls.get_movement_vector((0, 0)), [0, -1])
        self.controls.handle_keyboard('s', False)

        # Test A key
        self.controls.handle_keyboard('a', True)
        self.assertEqual(self.controls.get_movement_vector((0, 0)), [-1, 0])
        self.controls.handle_keyboard('a', False)

        # Test D key
        self.controls.handle_keyboard('d', True)
        self.assertEqual(self.controls.get_movement_vector((0, 0)), [1, 0])
        self.controls.handle_keyboard('d', False)

    def test_diagonal_movement(self):
        """Test diagonal WASD movement (W+D = up-right)."""
        # Press W and D simultaneously
        self.controls.handle_keyboard('w', True)
        self.controls.handle_keyboard('d', True)
        
        # Should be normalized vector
        vector = self.controls.get_movement_vector((0, 0))
        self.assertAlmostEqual(vector[0], 0.707, places=3)
        self.assertAlmostEqual(vector[1], 0.707, places=3)

        # Release both
        self.controls.handle_keyboard('w', False)
        self.controls.handle_keyboard('d', False)

    def test_mouse_movement(self):
        """Test mouse click movement."""
        # Test mouse click
        self.controls.handle_mouse_click((10, 10))
        vector = self.controls.get_movement_vector((0, 0))
        self.assertAlmostEqual(vector[0], 0.707, places=3)
        self.assertAlmostEqual(vector[1], 0.707, places=3)

    def test_combined_movement(self):
        """Test combined keyboard and mouse movement."""
        # Keyboard has priority
        self.controls.handle_keyboard('w', True)
        self.controls.handle_mouse_click((10, 10))
        self.assertEqual(self.controls.get_movement_vector((0, 0)), [0, 1])

        # Mouse movement when no keys pressed
        self.controls.handle_keyboard('w', False)
        vector = self.controls.get_movement_vector((0, 0))
        self.assertAlmostEqual(vector[0], 0.707, places=3)
        self.assertAlmostEqual(vector[1], 0.707, places=3)
        
        # Test mouse target reset when reached
        self.controls.handle_mouse_click((1, 1))
        self.controls.get_movement_vector((1, 1))
        self.assertIsNone(self.controls.target_position)


    def test_action_handlers(self):
        """Test keyboard action handlers."""
        # Mock action handlers in the dictionary
        self.controls.action_handlers['e'] = lambda: setattr(
            self, 'inventory_opened', True
        )
        self.controls.action_handlers['f'] = lambda: setattr(
            self, 'interacted', True
        )
        
        # Test inventory open
        self.controls.handle_keyboard('e', True)
        self.assertTrue(hasattr(self, 'inventory_opened'))
        
        # Test interaction
        self.controls.handle_keyboard('f', True)
        self.assertTrue(hasattr(self, 'interacted'))
        
        # Test no action on key release
        self.controls.handle_keyboard('i', False)
        self.assertFalse(hasattr(self, 'toggle_inventory'))


if __name__ == '__main__':
    unittest.main()
