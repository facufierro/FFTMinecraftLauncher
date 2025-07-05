"""Event system for the FFT Minecraft Launcher."""

from typing import Callable, Dict, List, Any, Optional
from enum import Enum


class EventType(Enum):
    """Enumeration of launcher events."""
    
    # Update events
    UPDATE_CHECK_STARTED = "update_check_started"
    UPDATE_CHECK_COMPLETED = "update_check_completed"
    UPDATE_CHECK_FAILED = "update_check_failed"
    
    UPDATE_STARTED = "update_started"
    UPDATE_PROGRESS = "update_progress"
    UPDATE_COMPLETED = "update_completed"
    UPDATE_FAILED = "update_failed"
    
    # Minecraft events
    MINECRAFT_LAUNCH_STARTED = "minecraft_launch_started"
    MINECRAFT_LAUNCH_COMPLETED = "minecraft_launch_completed"
    MINECRAFT_LAUNCH_FAILED = "minecraft_launch_failed"
    
    # Configuration events
    CONFIG_CHANGED = "config_changed"
    CONFIG_LOADED = "config_loaded"
    CONFIG_SAVED = "config_saved"
    
    # UI events
    UI_INITIALIZED = "ui_initialized"
    UI_CLOSED = "ui_closed"
    THEME_CHANGED = "theme_changed"


class LauncherEvents:
    """Event manager for the launcher."""
    
    def __init__(self):
        """Initialize the event manager."""
        self._listeners: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable[[Any], None]) -> None:
        """Subscribe to an event.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is fired
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Any], None]) -> None:
        """Unsubscribe from an event.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from listeners
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass  # Callback not in list
    
    def emit(self, event_type: EventType, data: Any = None) -> None:
        """Emit an event to all subscribers.
        
        Args:
            event_type: Type of event to emit
            data: Optional data to pass to listeners
        """
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    # Log error but don't stop other callbacks
                    print(f"Error in event callback for {event_type}: {e}")
    
    def clear_listeners(self, event_type: Optional[EventType] = None) -> None:
        """Clear listeners for a specific event type or all events.
        
        Args:
            event_type: Specific event type to clear, or None to clear all
        """
        if event_type is None:
            self._listeners.clear()
        elif event_type in self._listeners:
            self._listeners[event_type].clear()
    
    def get_listener_count(self, event_type: EventType) -> int:
        """Get the number of listeners for an event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of listeners for the event type.
        """
        return len(self._listeners.get(event_type, []))
