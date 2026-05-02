import sys
import os
import copy

# Hozzáadjuk a szülő mappát a path-hoz, hogy importálni tudjuk a modulokat
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Job, Operation, Machine
from simulator import Simulator
from scheduler import fifo_rule, spt_rule
from evaluator import Evaluator
from visualizer import Visualizer

def get_basic_data():
    """
    1. példa – Elégséges szint alapjai: 
    3 munka, 3 gép, végtelen puffer, folyamatos rendelkezésre állás.
    """
    machines = {
        "M1": Machine("M1"),
        "M2": Machine("M2"),
        "M3": Machine("M3")
    }

    # Due date nem feltétlenül kell ehhez. Legyen 20 mindenkinek.
    jobs = [
        Job(job_id="J1", due_date=20, operations=[
            Operation(operation_id="J1_Op1", machine_id="M1", duration=5),
            Operation(operation_id="J1_Op2", machine_id="M2", duration=4),
            Operation(operation_id="J1_Op3", machine_id="M3", duration=3)
        ]),
        Job(job_id="J2", due_date=20, operations=[
            Operation(operation_id="J2_Op1", machine_id="M2", duration=3),
            Operation(operation_id="J2_Op2", machine_id="M1", duration=6),
            Operation(operation_id="J2_Op3", machine_id="M3", duration=2)
        ]),
        Job(job_id="J3", due_date=20, operations=[
            Operation(operation_id="J3_Op1", machine_id="M3", duration=4),
            Operation(operation_id="J3_Op2", machine_id="M1", duration=2),
            Operation(operation_id="J3_Op3", machine_id="M2", duration=5)
        ])
    ]
    
    return jobs, machines

def run():
    print("\n--- 1. Mintapélda: Elégséges szint (Alapok) ---")
    evaluator = Evaluator()
    results = {}
    best_jobs = None

    # Tesztelés FIFO szabállyal
    jobs_fifo, machines_fifo = get_basic_data()
    sim_fifo = Simulator(jobs=jobs_fifo, machines=machines_fifo, dispatch_rule=fifo_rule)
    sim_fifo.run()
    results["FIFO"] = evaluator.calculate_metrics(jobs_fifo)

    # Tesztelés SPT szabállyal
    jobs_spt, machines_spt = get_basic_data()
    sim_spt = Simulator(jobs=jobs_spt, machines=machines_spt, dispatch_rule=spt_rule)
    sim_spt.run()
    results["SPT"] = evaluator.calculate_metrics(jobs_spt)
    best_jobs = jobs_spt  # Az SPT Gantt-ját mutatjuk meg

    # Eredmények kiíratása és megjelenítése
    Visualizer.print_comparison_table(results)
    
    print("\n[!] Gantt-diagram generálása az SPT stratégiához...")
    Visualizer.plot_gantt_chart(best_jobs, machines_spt, title="1. Példa - SPT Ütemezés")

if __name__ == "__main__":
    run()
