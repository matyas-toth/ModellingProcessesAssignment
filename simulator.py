import heapq
from typing import List, Dict, Callable, Optional
from models import Job, Machine, SimEvent, EventType, OpStatus

class Simulator:
    """
    Eseményvezérelt szimulációs motor.
    """
    def __init__(self, jobs: List[Job], machines: Dict[str, Machine], dispatch_rule: Callable[[List[Job], int], Job]):
        self.jobs = jobs
        self.machines = machines
        self.dispatch_rule = dispatch_rule
        self.current_time = 0
        self.event_queue: List[SimEvent] = []
        
        # Nyilvántartás a blokkolt gépekről (amik egy teli downstream pufferre várnak)
        # formátum: blocked_machines[blocked_machine_id] = target_machine_id
        self.blocked_machines: Dict[str, str] = {}

    def schedule_event(self, time: int, priority: int, event_type: EventType, payload: dict):
        """Új esemény ütemezése a prioritásos sorba."""
        event = SimEvent(time=time, priority=priority, event_type=event_type, payload=payload)
        heapq.heappush(self.event_queue, event)

    def initialize(self):
        """A szimuláció kezdőállapotának felépítése."""
        self.current_time = 0
        self.event_queue.clear()
        self.blocked_machines.clear()

        # 1. Minden munka érkezésének ütemezése
        for job in self.jobs:
            self.schedule_event(
                time=job.release_time,
                priority=10, # Alacsonyabb prioritás-szám = hamarabb fut le adott időpillanatban
                event_type=EventType.JOB_ARRIVAL,
                payload={"job": job}
            )

        # 2. Műszak események ütemezése (ha vannak)
        # Feltételezzük, hogy egy nagy maximum ideig fut a szimuláció (pl. 10000) ha ciklikus.
        # De itt most a megadott listán iterálunk.
        for m_id, machine in self.machines.items():
            if machine.availability_windows:
                for start_t, end_t in machine.availability_windows:
                    self.schedule_event(start_t, priority=1, event_type=EventType.SHIFT_START, payload={"machine_id": m_id})
                    self.schedule_event(end_t, priority=2, event_type=EventType.SHIFT_END, payload={"machine_id": m_id})
            else:
                # Ha nincsenek ablakok, a gép mindig be van kapcsolva
                machine.is_active_shift = True
                self.schedule_event(0, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": m_id})

    def run(self):
        """A szimuláció főciklusa. Addig fut, amíg van esemény a sorban."""
        self.initialize()
        
        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if event.event_type == EventType.JOB_ARRIVAL:
                self._handle_job_arrival(event.payload["job"])
            elif event.event_type == EventType.MACHINE_AVAILABLE:
                self._handle_machine_available(event.payload["machine_id"])
            elif event.event_type == EventType.OPERATION_COMPLETE:
                self._handle_operation_complete(event.payload["machine_id"], event.payload["job"])
            elif event.event_type == EventType.SHIFT_START:
                self._handle_shift_start(event.payload["machine_id"])
            elif event.event_type == EventType.SHIFT_END:
                self._handle_shift_end(event.payload["machine_id"])

    def _handle_job_arrival(self, job: Job):
        """Egy új munka megérkezik a rendszerbe."""
        op = job.get_current_operation()
        if not op:
            return
            
        machine = self.machines[op.machine_id]
        if machine.buffer.enqueue(job):
            # Sikeresen bekerült a pufferbe, szólunk a gépnek, hogy ellenőrizze tud-e dolgozni
            self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": machine.machine_id})
        else:
            # Ha az első gép puffere teli van (ritka, de előfordulhat)
            # A munka kint várakozik a gyár előtt egy virtuális végtelen sorban
            # Ezt most egy egyszerű újraszkedulálással (polling) oldjuk meg
            self.schedule_event(self.current_time + 1, priority=10, event_type=EventType.JOB_ARRIVAL, payload={"job": job})

    def _handle_machine_available(self, machine_id: str):
        """A gép felszabadult, megpróbál új munkát felvenni."""
        machine = self.machines[machine_id]
        
        # Ha nincs műszakban, vagy blokkolva van, vagy épp dolgozik, nem csinálunk semmit
        if not machine.is_active_shift or machine_id in self.blocked_machines or machine.current_job is not None:
            return

        if machine.buffer.queue:
            # Ütemezési szabály alkalmazása a sorra
            selected_job = self.dispatch_rule(machine.buffer.queue, self.current_time)
            machine.buffer.remove(selected_job)
            
            # Mivel kivettünk egy elemet, megnézzük, volt-e valaki blokkolva emiatt a puffer miatt
            self._check_blocked_machines(machine_id)
            
            machine.current_job = selected_job
            op = selected_job.get_current_operation()
            op.status = OpStatus.IN_PROGRESS
            op.start_time = self.current_time
            
            # Mikor lesz kész
            end_time = self.current_time + op.duration
            machine.busy_until = end_time
            
            self.schedule_event(end_time, priority=5, event_type=EventType.OPERATION_COMPLETE, payload={"machine_id": machine_id, "job": selected_job})

    def _handle_operation_complete(self, machine_id: str, job: Job):
        """Egy művelet befejeződött."""
        machine = self.machines[machine_id]
        op = job.get_current_operation()
        op.status = OpStatus.DONE
        op.end_time = self.current_time
        
        # Lépés a következő műveletre
        job.current_op_index += 1
        next_op = job.get_current_operation()
        
        if next_op is None:
            # A munka teljesen elkészült
            job.completion_time = self.current_time
            machine.current_job = None
            self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": machine_id})
        else:
            # Megpróbál bekerülni a következő gép pufferébe
            next_machine = self.machines[next_op.machine_id]
            if next_machine.buffer.enqueue(job):
                # Sikerült a továbbjutás
                machine.current_job = None
                self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": machine_id})
                self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": next_machine.machine_id})
            else:
                # BLOKKOLÁS: a következő puffer teli van
                self.blocked_machines[machine_id] = next_machine.machine_id

    def _check_blocked_machines(self, freed_machine_id: str):
        """Ellenőrzi, hogy van-e olyan gép, ami a most felszabadult pufferre várt."""
        unblocked = []
        for b_machine_id, target_machine_id in self.blocked_machines.items():
            if target_machine_id == freed_machine_id:
                # Megpróbáljuk újra betolni a jobot
                b_machine = self.machines[b_machine_id]
                job = b_machine.current_job
                t_machine = self.machines[target_machine_id]
                
                if t_machine.buffer.enqueue(job):
                    # Sikerült! A blokkolás feloldva
                    unblocked.append(b_machine_id)
                    b_machine.current_job = None
                    # A feloldott gép most már dolgozhat
                    self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": b_machine_id})
                    # És a cél gép is nézzen rá az új munkára
                    self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": target_machine_id})
        
        # Eltávolítjuk a feloldott gépeket a blokkoltak közül
        for m_id in unblocked:
            del self.blocked_machines[m_id]

    def _handle_shift_start(self, machine_id: str):
        """Műszak kezdete a gépen."""
        machine = self.machines[machine_id]
        machine.is_active_shift = True
        # Ha a műszak elkezdődik, és a gép amúgy szabad, ellenőrizze, tud-e dolgozni
        self.schedule_event(self.current_time, priority=5, event_type=EventType.MACHINE_AVAILABLE, payload={"machine_id": machine_id})

    def _handle_shift_end(self, machine_id: str):
        """Műszak vége a gépen."""
        machine = self.machines[machine_id]
        machine.is_active_shift = False
        # Ha éppen csinál valamit, a non-preemptive logika miatt azt még befejezi
        # Viszont új munkát már nem tud felvenni a következő SHIFT_START-ig.
