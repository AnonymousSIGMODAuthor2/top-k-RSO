import random
import time
from typing import Dict, Tuple
from alg.HPF_eq import HPFR, HPFR_div
from alg.baseline_iadu import base_precompute
from models import List, Place


def biased_sampling(S: List[Place], k: int, W, psS, sS) -> Tuple[List[Place], Dict[int, float], float, float]:
    
    # Preparation step
    # psS, sS, prep_time = base_precompute(S)
    
    # Random selection
    R_sampling, pruning_time = select_random(S, k)
    
    # Compute final scores
    score, sum_psS, sum_psR = HPFR(R_sampling, psS, sS, W, len(S))
    
    return R_sampling, score, sum_psS, sum_psR, 0.0, pruning_time


def biased_sampling_div(S: List[Place], k: int, W) -> Tuple[List[Place], Dict[int, float], float, float]:
    
    # Preparation step
    psS, sS, prep_time = base_precompute(S)
    
    # Random selection
    R_sampling, pruning_time = select_random(S, k)
    
    # Compute final scores
    score_rf, score_ps, sum_psS, sum_psR = HPFR_div(R_sampling, psS, sS, W, len(S))
    
    return R_sampling, score_rf + score_ps, score_rf, score_ps, sum_psS, sum_psR, pruning_time

def select_random(S: List[Place], k: int):
    
    pruning_time_start = time.time()
    sampled_S = random.sample(S, k)
    pruning_time = time.time() - pruning_time_start
    
    return  sampled_S, pruning_time