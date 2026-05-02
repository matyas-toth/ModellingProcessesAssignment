from typing import List, Dict
from models import Job

class Evaluator:
    """
    A szimuláció eredményeinek kiértékelésére szolgáló osztály.
    Kiszámítja az alapvető teljesítménymutatókat.
    """
    def __init__(self, w1: float = 0.25, w2: float = 0.25, w3: float = 0.25, w4: float = 0.25):
        # A négy cél súlyai a Wmix kiszámításához
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        self.w4 = w4

    def calculate_metrics(self, jobs: List[Job]) -> Dict[str, float]:
        """Kiszámítja a 4 alapvető optimalizálási célt és a súlyozott összeget (Wmix)."""
        cmax = 0      # Makespan
        tmax = 0      # Maximális csúszás
        sum_ti = 0    # Csúszások összege
        nt = 0        # Késő munkák száma
        
        for job in jobs:
            if job.completion_time is None:
                # Ha a munka valamiért nem fejeződött be (pl. végtelen blokkolás/deadlock miatt)
                return {
                    "Cmax": float('inf'),
                    "Tmax": float('inf'),
                    "SumTi": float('inf'),
                    "NT": len(jobs),
                    "Wmix": float('inf')
                }
                
            cmax = max(cmax, job.completion_time)
            
            t_i = job.tardiness
            tmax = max(tmax, t_i)
            sum_ti += t_i
            
            if t_i > 0:
                nt += 1
                
        wmix = self.w1 * cmax + self.w2 * tmax + self.w3 * sum_ti + self.w4 * nt
        
        return {
            "Cmax": cmax,
            "Tmax": tmax,
            "SumTi": sum_ti,
            "NT": nt,
            "Wmix": wmix
        }
        
    def get_wmix(self, jobs: List[Job]) -> float:
        """Közvetlenül a Wmix-et adja vissza a prediktív ütemező (Hill Climbing) optimalizációjához."""
        return self.calculate_metrics(jobs)["Wmix"]
