import random
import copy
from typing import List, Dict, Callable, Optional
from models import Job

# Reaktív Ütemezési Szabályok

def fifo_rule(queue: List[Job], current_time: int) -> Job:
    """FIFO (First In, First Out): A legrégebben várakozó munka."""
    return queue[0]

def spt_rule(queue: List[Job], current_time: int) -> Job:
    """SPT (Shortest Processing Time): A legrövidebb aktuális műveleti idejű munka."""
    return min(queue, key=lambda j: j.get_current_operation().duration)

def edd_rule(queue: List[Job], current_time: int) -> Job:
    """EDD (Earliest Due Date): A legkorábbi határidejű munka kap elsőbbséget."""
    return min(queue, key=lambda j: j.due_date)

def cr_rule(queue: List[Job], current_time: int) -> Job:
    """
    CR (Critical Ratio): (due_date - now) / remaining_processing_time.
    Minél kisebb, annál kritikusabb, tehát a legkisebb kapja az elsőbbséget.
    """
    def calc_cr(j: Job):
        rem_time = sum(op.duration for op in j.operations[j.current_op_index:])
        if rem_time == 0:
            return float('-inf')
        return (j.due_date - current_time) / rem_time
    return min(queue, key=calc_cr)

def slack_rule(queue: List[Job], current_time: int) -> Job:
    """
    SLACK (Minimum Slack Time): due_date - now - remaining_time.
    A legkisebb tartalékidejű munka kap elsőbbséget.
    """
    def calc_slack(j: Job):
        rem_time = sum(op.duration for op in j.operations[j.current_op_index:])
        return j.due_date - current_time - rem_time
    return min(queue, key=calc_slack)

def random_rule(queue: List[Job], current_time: int) -> Job:
    """RANDOM: Véletlenszerű döntés."""
    return random.choice(queue)


# Prediktív Ütemező

class PredictiveScheduler:
    """
    A prediktív ütemező előre meghatározza a munkák végrehajtási sorrendjét az összes gépen.
    Lokális keresővel (Hill Climbing) optimalizálja a súlyozott összesített célfüggvényt (Wmix).
    """
    def __init__(self, original_jobs: List[Job], original_machines: dict, evaluator_func: Callable, max_iterations: int = 50):
        self.original_jobs = original_jobs
        self.original_machines = original_machines
        self.evaluator_func = evaluator_func
        self.max_iterations = max_iterations
        self.best_sequences: Dict[str, List[str]] = {}
        
    def generate_initial_sequences(self) -> Dict[str, List[str]]:
        """Mohó (Greedy) kezdeti megoldás generálása: EDD szerint minden gépen."""
        sequences = {m_id: [] for m_id in self.original_machines.keys()}
        
        machine_jobs = {m_id: [] for m_id in self.original_machines.keys()}
        for job in self.original_jobs:
            for op in job.operations:
                if job not in machine_jobs[op.machine_id]:
                    machine_jobs[op.machine_id].append(job)
                    
        for m_id, jobs in machine_jobs.items():
            sorted_jobs = sorted(jobs, key=lambda j: j.due_date)
            sequences[m_id] = [j.job_id for j in sorted_jobs]
            
        return sequences

    def get_dispatch_rule_for_sequences(self, sequences: Dict[str, List[str]]) -> Callable[[List[Job], int], Job]:
        """Készít egy olyan reaktív szabályt, ami a kiszámolt fix sorrendet követi."""
        def sequence_rule(queue: List[Job], current_time: int) -> Job:
            if not queue: return None
            m_id = queue[0].get_current_operation().machine_id
            seq = sequences[m_id]
            
            best_job = queue[0]
            best_idx = float('inf')
            
            for job in queue:
                try:
                    idx = seq.index(job.job_id)
                except ValueError:
                    idx = float('inf')
                if idx < best_idx:
                    best_idx = idx
                    best_job = job
                    
            return best_job
            
        return sequence_rule

    def evaluate_sequences(self, sequences: Dict[str, List[str]]) -> float:
        """Kiszimulálja az adott szekvenciát és visszaadja a célfüggvény (Wmix) értékét."""
        jobs_copy = copy.deepcopy(self.original_jobs)
        machines_copy = copy.deepcopy(self.original_machines)
        
        from simulator import Simulator
        rule = self.get_dispatch_rule_for_sequences(sequences)
        sim = Simulator(jobs=jobs_copy, machines=machines_copy, dispatch_rule=rule)
        
        try:
            # 100000 limit, hogy elkerüljük a végtelen ciklust deadlock esetén
            sim.run()
            
            # Ellenőrizzük, hogy minden munka befejeződött-e (deadlock detektálás)
            for j in jobs_copy:
                if not j.is_completed():
                    return float('inf')
                    
            return self.evaluator_func(jobs_copy)
        except Exception:
            return float('inf')

    def optimize(self) -> Dict[str, List[str]]:
        """Lokális kereső (Hill Climbing) algoritmus futtatása."""
        current_seq = self.generate_initial_sequences()
        current_score = self.evaluate_sequences(current_seq)
        
        self.best_sequences = copy.deepcopy(current_seq)
        best_score = current_score
        
        for _ in range(self.max_iterations):
            neighbor_seq = copy.deepcopy(current_seq)
            m_id = random.choice(list(neighbor_seq.keys()))
            seq = neighbor_seq[m_id]
            
            # Szomszéd generálása: két munka felcserélése
            if len(seq) >= 2:
                idx1, idx2 = random.sample(range(len(seq)), 2)
                seq[idx1], seq[idx2] = seq[idx2], seq[idx1]
                
            neighbor_score = self.evaluate_sequences(neighbor_seq)
            
            # Ha jobb a szomszéd, elfogadjuk (kisebb Wmix a cél)
            if neighbor_score < current_score:
                current_seq = neighbor_seq
                current_score = neighbor_score
                
                if neighbor_score < best_score:
                    best_score = neighbor_score
                    self.best_sequences = copy.deepcopy(current_seq)
                    
        return self.best_sequences
