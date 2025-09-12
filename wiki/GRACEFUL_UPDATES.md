# Graceful Update System

The LED Matrix project now includes a graceful update system that prevents lag during scrolling displays by deferring updates until the display is not actively scrolling.

## Overview

When displays like the odds ticker, stock ticker, or news ticker are actively scrolling, performing API updates or data fetching can cause visual lag or stuttering. The graceful update system solves this by:

1. **Tracking scrolling state** - The system monitors when displays are actively scrolling
2. **Deferring updates** - Updates that might cause lag are deferred during scrolling periods
3. **Processing when safe** - Deferred updates are processed when scrolling stops or during non-scrolling periods
4. **Priority-based execution** - Updates are executed in priority order when processed

## How It Works

### Scrolling State Tracking

The `DisplayManager` class now includes scrolling state tracking:

```python
# Signal when scrolling starts
display_manager.set_scrolling_state(True)

# Signal when scrolling stops
display_manager.set_scrolling_state(False)

# Check if currently scrolling
if display_manager.is_currently_scrolling():
    # Defer updates
    pass
```

### Deferred Updates

Updates can be deferred using the `defer_update` method:

```python
# Defer an update with priority
display_manager.defer_update(
    lambda: self._perform_update(),
    priority=1  # Lower numbers = higher priority
)
```

### Automatic Processing

Deferred updates are automatically processed when:
- A display signals it's not scrolling
- The main loop processes updates during non-scrolling periods
- The inactivity threshold is reached (default: 2 seconds)

## Implementation Details

### Display Manager Changes

The `DisplayManager` class now includes:

- `set_scrolling_state(is_scrolling)` - Signal scrolling state changes
- `is_currently_scrolling()` - Check if display is currently scrolling
- `defer_update(update_func, priority)` - Defer an update function
- `process_deferred_updates()` - Process all pending deferred updates
- `get_scrolling_stats()` - Get current scrolling statistics

### Manager Updates

The following managers have been updated to use the graceful update system:

#### Odds Ticker Manager
- Defers API updates during scrolling
- Signals scrolling state during display
- Processes deferred updates when not scrolling

#### Stock Manager
- Defers stock data updates during scrolling
- Always signals scrolling state (continuous scrolling)
- Priority 2 for stock updates

#### Stock News Manager
- Defers news data updates during scrolling
- Signals scrolling state during display
- Priority 2 for news updates

### Display Controller Changes

The main display controller now:
- Checks scrolling state before updating modules
- Defers scrolling-sensitive updates during scrolling periods
- Processes deferred updates in the main loop
- Continues non-scrolling-sensitive updates normally

## Configuration

The system uses these default settings:

- **Inactivity threshold**: 2.0 seconds
- **Update priorities**:
  - Priority 1: Odds ticker updates
  - Priority 2: Stock and news updates
  - Priority 3+: Other updates

## Benefits

1. **Smoother Scrolling** - No more lag during ticker scrolling
2. **Better User Experience** - Displays remain responsive during updates
3. **Efficient Resource Usage** - Updates happen when the system is idle
4. **Priority-Based** - Important updates are processed first
5. **Automatic** - No manual intervention required

## Testing

You can test the graceful update system using the provided test script:

```bash
python test_graceful_updates.py
```

This script demonstrates:
- Deferring updates during scrolling
- Processing updates when not scrolling
- Priority-based execution
- Inactivity threshold behavior

## Debugging

To debug the graceful update system, enable debug logging:

```python
import logging
logging.getLogger('src.display_manager').setLevel(logging.DEBUG)
```

The system will log:
- When scrolling state changes
- When updates are deferred
- When deferred updates are processed
- Current scrolling statistics

## Future Enhancements

Potential improvements to the system:

1. **Configurable thresholds** - Allow users to adjust inactivity thresholds
2. **More granular priorities** - Add more priority levels for different update types
3. **Update batching** - Group similar updates to reduce processing overhead
4. **Performance metrics** - Track and report update deferral statistics
5. **Web interface integration** - Show deferred update status in the web UI
