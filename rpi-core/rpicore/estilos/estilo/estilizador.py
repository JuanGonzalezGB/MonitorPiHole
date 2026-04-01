# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

from abc import ABC, abstractmethod


class Estilo(ABC):
    @abstractmethod
    def colorBg(self) : pass
    @abstractmethod
    def colorBg(self): pass
    @abstractmethod
    def colorBg2(self): pass
    @abstractmethod
    def colorBorder(self): pass
    @abstractmethod
    def colorColorOk(self):  pass
    @abstractmethod
    def colorColorMid(self): pass
    @abstractmethod
    def colorColorBad(self):   pass 
    @abstractmethod
    def colorColor1(self):  pass 
    @abstractmethod
    def colorColor2(self):   pass
    @abstractmethod
    def colorColor3(self):  pass
    @abstractmethod
    def colorMuted(self): pass
    @abstractmethod
    def colorBoton(self):  pass
    @abstractmethod
    def getNombre(self):  pass