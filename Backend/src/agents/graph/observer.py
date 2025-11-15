"""
Observer Pattern: For logging and monitoring agent execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime
import logging


class Observer(ABC):
    """Abstract observer interface."""
    
    @abstractmethod
    def update(self, event: str, data: Dict[str, Any]):
        """Update observer with event data."""
        pass


class LoggingObserver(Observer):
    """Observer that logs events to console/file."""
    
    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("lyra.agents")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def update(self, event: str, data: Dict[str, Any]):
        """Log the event."""
        message = f"[{event}] {data.get('message', '')}"
        level = data.get('level', 'INFO').upper()
        
        if level == 'DEBUG':
            self.logger.debug(message)
        elif level == 'INFO':
            self.logger.info(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)
        else:
            self.logger.info(message)


class MetricsObserver(Observer):
    """Observer that tracks metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'tool_calls': {},
            'errors': [],
            'execution_times': {},
            'start_time': None,
            'end_time': None
        }
    
    def update(self, event: str, data: Dict[str, Any]):
        """Update metrics."""
        if event == 'tool_call':
            tool_name = data.get('tool_name', 'unknown')
            if tool_name not in self.metrics['tool_calls']:
                self.metrics['tool_calls'][tool_name] = 0
            self.metrics['tool_calls'][tool_name] += 1
            
            if 'execution_time' in data:
                if tool_name not in self.metrics['execution_times']:
                    self.metrics['execution_times'][tool_name] = []
                self.metrics['execution_times'][tool_name].append(data['execution_time'])
        
        elif event == 'error':
            self.metrics['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': data.get('error', ''),
                'context': data.get('context', {})
            })
        
        elif event == 'start':
            self.metrics['start_time'] = datetime.now().isoformat()
        
        elif event == 'end':
            self.metrics['end_time'] = datetime.now().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def reset(self):
        """Reset metrics."""
        self.metrics = {
            'tool_calls': {},
            'errors': [],
            'execution_times': {},
            'start_time': None,
            'end_time': None
        }


class Subject:
    """Subject that notifies observers."""
    
    def __init__(self):
        self._observers: list[Observer] = []
    
    def attach(self, observer: Observer):
        """Attach an observer."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        """Detach an observer."""
        self._observers.remove(observer)
    
    def notify(self, event: str, data: Dict[str, Any]):
        """Notify all observers."""
        for observer in self._observers:
            try:
                observer.update(event, data)
            except Exception as e:
                # Don't let observer errors break the system
                print(f"Error notifying observer: {e}")

