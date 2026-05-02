from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

# Eseménytípusok definíciója
class EventType(Enum):
    JOB_ARRIVAL = 1
    MACHINE_AVAILABLE = 2
    OPERATION_COMPLETE = 3
    SHIFT_START = 4
    SHIFT_END = 5

# Művelet státuszok
class OpStatus(Enum):
    PENDING = 1
    IN_PROGRESS = 2
    DONE = 3

@dataclass
class Operation:
    """
    Egyetlen műveletet ír le, amelyet egy adott gépen kell elvégezni.
    """
    operation_id: str
    machine_id: str
    duration: int
    status: OpStatus = OpStatus.PENDING
    start_time: Optional[int] = None
    end_time: Optional[int] = None

@dataclass
class Job:
    """
    Egy munkát reprezentál, amely műveletek rendezett sorozatából áll.
    """
    job_id: str
    operations: List[Operation]
    due_date: int
    release_time: int = 0
    current_op_index: int = 0
    completion_time: Optional[int] = None
    
    @property
    def tardiness(self) -> int:
        """Kiszámítja a késést (tardiness). Ha nincs még befejezve, 0-t ad."""
        if self.completion_time is None:
            return 0
        return max(0, self.completion_time - self.due_date)

    def is_completed(self) -> bool:
        """Megadja, hogy a munka minden művelete elkészült-e."""
        return self.current_op_index >= len(self.operations)
        
    def get_current_operation(self) -> Optional[Operation]:
        """Visszaadja a soron következő műveletet, ha van ilyen."""
        if not self.is_completed():
            return self.operations[self.current_op_index]
        return None

class Buffer:
    """
    Korlátozott kapacitású várakozási sort valósít meg egy gép előtt (FIFO alapokon).
    Végtelen kapacitás esetén a capacity None (vagy nagyon nagy szám).
    """
    def __init__(self, capacity: Optional[int] = None):
        self.capacity = capacity
        self.queue: List[Job] = []

    def is_full(self) -> bool:
        """Igazzal tér vissza, ha a tároló betelt."""
        if self.capacity is None:
            return False
        return len(self.queue) >= self.capacity

    def enqueue(self, job: Job) -> bool:
        """Egy munkát ad a sorhoz. Visszatérési értéke True, ha sikerült (volt hely)."""
        if not self.is_full():
            self.queue.append(job)
            return True
        return False

    def dequeue(self) -> Optional[Job]:
        """A következő munkát (FIFO alapon) veszi ki a sorból. Ha üres, None."""
        if self.queue:
            return self.queue.pop(0)
        return None
        
    def remove(self, job: Job):
        """Egy adott munka törlése a tárolóból (pl. prediktív ütemező miatt)."""
        if job in self.queue:
            self.queue.remove(job)

class Machine:
    """
    Egy dedikált erőforrást (gépet, munkahelyet) modellez.
    """
    def __init__(self, machine_id: str, capacity: Optional[int] = None, availability_windows: Optional[List[Tuple[int, int]]] = None):
        self.machine_id = machine_id
        self.buffer = Buffer(capacity)
        # Ha nincsenek megadva rendelkezésre állási ablakok, a gép mindig aktív.
        self.availability_windows = availability_windows if availability_windows else []
        self.current_job: Optional[Job] = None
        self.is_active_shift: bool = True if not availability_windows else False
        self.busy_until: int = 0

    def is_available(self, current_time: int) -> bool:
        """Visszaadja, hogy a gép jelenleg szabad-e (nincs rajta munka) és műszakban van-e."""
        return self.current_job is None and self.is_active_shift

@dataclass(order=True)
class SimEvent:
    """
    Az eseményvezérelt szimuláció alapegysége, amit a prioritásos sorhoz használunk.
    A rendezés a 'time' (időpont) és utána a prioritás alapján történik,
    hogy egyező időpontnál bizonyos események hamarabb fussanak le (pl. SHIFT_START).
    """
    time: int
    priority: int
    event_type: EventType = field(compare=False)
    payload: dict = field(compare=False)
