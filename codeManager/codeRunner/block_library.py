import requests
import os
import time
from typing import Tuple, Optional

class Block:
    """A single block in the BlockDisplay matrix"""
    
    def __init__(self, x: int, y: int, display_id: str):
        self.x = x
        self.y = y
        self.display_id = display_id
        self._color = (255, 255, 255)  # RGB tuple
        self._brightness = 1.0  # 0-1 float
        self._on = False  # boolean
    
    @property
    def color(self) -> Tuple[int, int, int]:
        return self._color
    
    @color.setter
    def color(self, value: Tuple[int, int, int]):
        if self._color != value:
            self._color = value
            self._notify_change('color', value)
    
    @property
    def brightness(self) -> float:
        return self._brightness
    
    @brightness.setter
    def brightness(self, value: float):
        if self._brightness != value:
            self._brightness = max(0.0, min(1.0, value))  # Clamp to 0-1
            self._notify_change('brightness', self._brightness)
    
    @property
    def on(self) -> bool:
        return self._on
    
    @on.setter
    def on(self, value: bool):
        if self._on != value:
            self._on = bool(value)
            self._notify_change('on', self._on)
    
    def _notify_change(self, property_name: str, value):
        """Send change notification to codeManager"""
        try:
            user_id = os.environ.get('BLOCK_USER_ID')
            if not user_id:
                return
            
            payload = {
                'display_id': self.display_id,
                'user_id': user_id,
                'block_x': self.x,
                'block_y': self.y,
                'property': property_name,
                'value': value,
                'timestamp': time.time()
            }
            
            # Send HTTP POST to codeManager
            requests.post(
                'http://manager:5001/block_update',
                json=payload,
                timeout=1.0  # Short timeout to avoid blocking
            )
        except Exception as e:
            # Silently ignore network errors to avoid breaking user code
            pass

class BlockDisplay:
    """8x8 matrix of Blocks with change tracking"""
    
    def __init__(self, display_id: str = None):
        self.display_id = display_id or f"display_{int(time.time() * 1000)}"
        self._blocks = {}
        
        # Initialize 8x8 matrix of blocks
        for x in range(8):
            for y in range(8):
                self._blocks[(x, y)] = Block(x, y, self.display_id)
    
    def __getitem__(self, key):
        """Allow access like display[x, y] or display[x][y]"""
        if isinstance(key, tuple) and len(key) == 2:
            x, y = key
            if 0 <= x < 8 and 0 <= y < 8:
                return self._blocks[(x, y)]
            else:
                raise IndexError(f"Block coordinates ({x}, {y}) out of range (0-7)")
        else:
            raise TypeError("BlockDisplay indices must be (x, y) tuple")
    
    def __setitem__(self, key, value):
        """Allow setting like display[x, y] = block"""
        if isinstance(key, tuple) and len(key) == 2:
            x, y = key
            if 0 <= x < 8 and 0 <= y < 8:
                if isinstance(value, Block):
                    self._blocks[(x, y)] = value
                else:
                    raise TypeError("Value must be a Block instance")
            else:
                raise IndexError(f"Block coordinates ({x}, {y}) out of range (0-7)")
        else:
            raise TypeError("BlockDisplay indices must be (x, y) tuple")
    
    def __setattr__(self, name, value):
        """Override __setattr__ to track changes to Block properties"""
        # Handle normal attributes
        if name.startswith('_') or name in ['display_id', '_blocks']:
            super().__setattr__(name, value)
            return
        
        # For Block property access, delegate to the specific block
        if isinstance(name, str) and '.' in name:
            # Handle cases like "blocks[0,0].color"
            parts = name.split('.')
            if len(parts) == 2 and parts[0].startswith('blocks[') and parts[0].endswith(']'):
                coords_str = parts[0][7:-1]  # Extract coordinates
                try:
                    x, y = map(int, coords_str.split(','))
                    block = self[x, y]
                    setattr(block, parts[1], value)
                    return
                except (ValueError, IndexError):
                    pass
        
        # Default behavior for other attributes
        super().__setattr__(name, value)
    
    def get_block(self, x: int, y: int) -> Block:
        """Get block at coordinates (x, y)"""
        if 0 <= x < 8 and 0 <= y < 8:
            return self._blocks[(x, y)]
        else:
            raise IndexError(f"Block coordinates ({x}, {y}) out of range (0-7)")
    
    def set_block_color(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set color of block at (x, y)"""
        self[x, y].color = color
    
    def set_block_brightness(self, x: int, y: int, brightness: float):
        """Set brightness of block at (x, y)"""
        self[x, y].brightness = brightness
    
    def set_block_on(self, x: int, y: int, on: bool):
        """Set on/off state of block at (x, y)"""
        self[x, y].on = on
    
    def clear(self):
        """Turn off all blocks"""
        for x in range(8):
            for y in range(8):
                self[x, y].on = False
    
    def fill(self, color: Tuple[int, int, int] = (255, 255, 255), brightness: float = 1.0):
        """Fill all blocks with same color and brightness"""
        for x in range(8):
            for y in range(8):
                self[x, y].color = color
                self[x, y].brightness = brightness
                self[x, y].on = True
