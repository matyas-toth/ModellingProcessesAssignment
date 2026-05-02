import sys
import os
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Job, Operation, Machine
from simulator import Simulator
from scheduler import fifo_rule, spt_rule, edd_rule, cr_rule, slack_rule, PredictiveScheduler
from evaluator import Evaluator
from visualizer import Visualizer

def get_multi_data():
    """
    4. példa – Jeles szint:
    6 munka, 4 gép, határidőkkel.
    Többcélú összehasonlítás.
    """
    machines = {f"M{i}": Machine(f"M{i}") for i in range(1, 5)}

    jobs = [
        Job(job_id="J1", due_date=40, operations=[
            Operation("J1_1", "M1", 4), Operation("J1_2", "M2", 5), Operation("J1_3", "M3", 3), Operation("J1_4", "M4", 4)
        ]),
        Job(job_id="J2", due_date=45, operations=[
            Operation("J2_1", "M2", 3), Operation("J2_2", "M1", 6), Operation("J2_3", "M4", 2), Operation("J2_4", "M3", 5)
        ]),
        Job(job_id="J3", due_date=35, operations=[
            Operation("J3_1", "M3", 6), Operation("J3_2", "M4", 2), Operation("J3_3", "M1", 4), Operation("J3_4", "M2", 3)
        ]),
        Job(job_id="J4", due_date=55, operations=[
            Operation("J4_1", "M4", 5), Operation("J4_2", "M3", 3), Operation("J4_3", "M2", 4), Operation("J4_4", "M1", 2)
        ]),
        Job(job_id="J5", due_date=50, operations=[
            Operation("J5_1", "M1", 3), Operation("J5_2", "M3", 4), Operation("J5_3", "M2", 5), Operation("J5_4", "M4", 3)
        ]),
        Job(job_id="J6", due_date=60, operations=[
            Operation("J6_1", "M2", 4), Operation("J6_2", "M4", 5), Operation("J6_3", "M1", 3), Operation("J6_4", "M3", 6)
        ])
    ]
    
    return jobs, machines

def run():
    print("\n--- 4. Mintapélda: Jeles szint (Többcélú optimalizálás és Prediktív kereső) ---")
    
    rules = {
        "FIFO": fifo_rule,
        "SPT": spt_rule,
        "EDD": edd_rule,
        "CR": cr_rule,
        "SLACK": slack_rule
    }
    
    evaluator = Evaluator(w1=0.25, w2=0.25, w3=0.25, w4=0.25)
    results = {}
    
    # 1. Reaktív szabályok futtatása
    for name, rule in rules.items():
        jobs, machines = get_multi_data()
        sim = Simulator(jobs=jobs, machines=machines, dispatch_rule=rule)
        sim.run()
        results[name] = evaluator.calculate_metrics(jobs)
        
    # 2. Prediktív (Hill Climbing) futtatása
    print("[!] Prediktív ütemező (Hill Climbing) futtatása, ez eltarthat pár másodpercig...")
    jobs_pred, machines_pred = get_multi_data()
    pred_scheduler = PredictiveScheduler(
        original_jobs=jobs_pred, 
        original_machines=machines_pred, 
        evaluator_func=evaluator.get_wmix, 
        max_iterations=100
    )
    best_seq = pred_scheduler.optimize()
    
    # A legjobb szekvencia tesztelése a végső eredményekhez
    final_jobs, final_machines = get_multi_data()
    pred_rule = pred_scheduler.get_dispatch_rule_for_sequences(best_seq)
    sim_pred = Simulator(jobs=final_jobs, machines=final_machines, dispatch_rule=pred_rule)
    sim_pred.run()
    
    results["Hill Climbing (Prediktív)"] = evaluator.calculate_metrics(final_jobs)
    
    Visualizer.print_comparison_table(results)
    
    print("\n[!] Gantt-diagram generálása a Prediktív ütemező eredményéhez...")
    Visualizer.plot_gantt_chart(final_jobs, final_machines, title="4. Példa - Hill Climbing Ütemezés")

if __name__ == "__main__":
    run()
