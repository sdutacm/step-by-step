from typing import List

from .base import SourceBase
from .sdut import SDUT
from .vj import VJ

sources: List[SourceBase] = [SDUT, VJ]
