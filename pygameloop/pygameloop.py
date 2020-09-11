from collections.abc import MutableMapping
from typing import Any, Iterable, Mapping, Type, Union

import pygame
from pygame.locals import *


class _Configuration(dict):
    def __dir__(self) -> Iterable[str]:
        result = super().__dir__()
        result.extend(self.keys())
        return result

    def __getattr__(self, name: str) -> Any:
        return self[name]

    def __setattr__(self, name: str, value: Any):
        self[name] = value


class _Wrapper:
    __slots__ = ['_wrapped', '_allow_set']

    def __init__(self, wrapped: Any, allow_set=True):
        super().__setattr__('_wrapped', wrapped)
        super().__setattr__('_allow_set', allow_set)

    def __dir__(self) -> Iterable[str]:
        return self.__getattribute__('_wrapped').__dir__()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__getattribute__('_wrapped'), name)

    def __setattr__(self, name: str, value: Any):
        if self.__getattribute__('_allow_set'):
            setattr(self.__getattribute__('_wrapped'), name, value)
        else:
            raise ReferenceError('Setting attributes on wrapped objects is disallowed')


class GameObject:
    pass


class _Game:
    __slots__ = ['_objects', '_coroutines', '_config', '_running', '_to_destroy', '_should_destroy_all']

    def __init__(self):
        self._objects = []
        self._coroutines = []
        self._config = _generate_default_config()
        self._running = False
        self._to_destroy = []
        self._should_destroy_all = False

    @property
    def config(self) -> _Configuration:
        return self._config

    @config.setter
    def config(self, new_config: Mapping) -> _Configuration:
        self._config.clear()
        self._config.update(new_config)

    def _call_on_one(self, obj: GameObject, func: str, *args):
        builtin_func = f'__{GameObject.__name__}_{func}'
        if hasattr(obj, builtin_func):
            getattr(obj, builtin_func)(*args)
        if hasattr(obj, func):
            getattr(obj, func)(*args)

    def _call_on_all(self, func: str, *args):
        for obj in self._objects:
            self._call_on_one(obj, func, *args)

    def instantiate(self, klass: Type[GameObject]) -> GameObject:
        obj = klass()
        self._call_on_one(obj, 'awake')
        if self._running:
            self._call_on_one(obj, 'start')
        self._objects.append(obj)
        return obj

    def destroy_immediate(self, obj: Union[int, GameObject]):
        self._call_on_one(obj, 'on_destroy')
        if isinstance(obj, int):
            obj = self._objects.pop(obj)
        else:
            self._objects.remove(obj)

    def destroy(self, obj: Union[int, GameObject]):
        self._to_destroy.append(obj)

    def destroy_all_immediate(self):
        self._call_on_all('on_destroy')
        self._objects.clear()

    def destroy_all(self):
        self._should_destroy_all = True

    def run(self):
        pygame.init()
        clock = pygame.time.Clock()
        primary_surface = pygame.display.set_mode(
            self._config['screen_size'],
            self._config['screen_flags'],
            self._config['screen_depth'],
            self._config['screen_display']
        )
        window.__init__(primary_surface)
        self._call_on_all('start')
        _generate_default_time()
        self._running = True
        while self._running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self._running = False
                else:
                    self._call_on_all(f'on_{pygame.event.event_name(event.type).lower()}', event)
            frame_ms = clock.tick(self._config['target_frame_rate'])
            time['delta_time'] = frame_ms / 1000.0
            time['frame_count'] += 1
            time['time'] += time.delta_time
            self._call_on_all('update')
            time['fixed_unscaled_delta_time'] += time.delta_time
            if time['fixed_unscaled_delta_time'] >= time.fixed_delta_time:
                self._call_on_all('fixed_update')
                time['fixed_unscaled_delta_time'] = 0.0
            self._call_on_all('late_update')
            if self._config['background_color'] is not None:
                primary_surface.fill(self._config['background_color'])
            self._call_on_all('draw', primary_surface)
            pygame.display.update()
            if self._should_destroy_all:
                self.destroy_all_immediate()
                self._should_destroy_all = False
                self._to_destroy.clear()
            elif self._to_destroy:
                for obj in self._to_destroy:
                    self.destroy_immediate(obj)
                self._to_destroy.clear()
        self._call_on_all('on_application_suspend')
        self._call_on_all('on_application_quit')
        self.destroy_all_immediate()
        time.clear()
        pygame.quit()

    def quit(self):
        self._running = False


def Scene() -> _Game:
    singleton_scene.__init__()
    return singleton_scene


def _generate_default_config() -> _Configuration:
    config['target_frame_rate'] = -1
    config['background_color'] = (255, 255, 255)
    config['screen_size'] = (640, 480)
    config['screen_flags'] = 0
    config['screen_depth'] = 0
    config['screen_display'] = 0
    return config


def _generate_default_time():
    time['delta_time'] = 0.0
    time['fixed_delta_time'] = 0.02
    time['fixed_unscaled_delta_time'] = 0.0
    time['frame_count'] = 0
    time['time'] = 0.0


singleton_scene : _Game = _Game.__new__(_Game)
config = _Configuration()
time: _Configuration = _Configuration()
window: pygame.Surface = _Wrapper.__new__(_Wrapper)

__all__ = [
    'Scene', 'GameObject',
    'singleton_scene', 'time'
]
