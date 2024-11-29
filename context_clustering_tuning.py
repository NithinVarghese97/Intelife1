import optuna
import numpy as np
from sklearn.model_selection import cross_val_score
from context_clustering import cluster_sentences

def objective(trial):
    """
    Objective function for Optuna hyperparameter optimization
    
    Parameters:
    -----------
    trial : optuna.trial.Trial
        A single trial of hyperparameter configuration
    
    Returns:
    --------
    float
        Average coherence score (to be maximized)
    """
    # Define hyperparameter search space
    config = {
        'min_cluster_size': trial.suggest_int('min_cluster_size', 3, 20),
        'min_samples': trial.suggest_int('min_samples', 3, 20),
        'cluster_selection_epsilon': trial.suggest_float('cluster_selection_epsilon', 0.0, 0.5),
        'cluster_selection_method': trial.suggest_categorical(
            'cluster_selection_method', 
            ["leaf", "eom"]
        ),
        'ngram_range': trial.suggest_categorical('ngram_range', [
            (1, 1), (1, 2), (1, 3)
        ]),
        'max_df': trial.suggest_float('max_df', 0.5, 1.0),
    }
    
    # Perform clustering
    try:
        groups, coherence = cluster_sentences(sentences, config)
        
        # Penalize very small or very large number of groups
        group_penalty = min(
            1.0, 
            max(0.1, 1 - abs(len(groups) - len(sentences) * 0.1) / len(sentences))
        )
        
        return coherence * group_penalty
    
    except Exception as e:
        print(f"Trial failed: {e}")
        return -np.inf

def tune_hyperparameters(
    sentences, 
    n_trials=100, 
    timeout=3600,  # 1 hour timeout
    show_progress_bar=True
):
    """
    Perform hyperparameter tuning using Optuna
    
    Parameters:
    -----------
    sentences : list of str
        List of sentences to cluster
    n_trials : int, optional
        Number of trials to run
    timeout : int, optional
        Maximum time (in seconds) to run optimization
    show_progress_bar : bool, optional
        Whether to show Optuna progress bar
    
    Returns:
    --------
    dict
        Best hyperparameters and corresponding coherence score
    """
    # Create a study object and optimize the objective function
    study = optuna.create_study(direction='maximize')
    study.optimize(
        objective, 
        n_trials=n_trials, 
        timeout=timeout,
        show_progress_bar=show_progress_bar
    )
    
    # Print results
    print("Best trial:")
    trial = study.best_trial
    
    print(f"  Value (Coherence Score): {trial.value}")
    print("  Params: ")
    for key, value in trial.params.items():
        print(f"    {key}: {value}")
    
    return {
        'best_params': trial.params,
        'best_score': trial.value
    }

if __name__ == "__main__":
    # Load sentences from a text file
    with open('app/text/output.txt', 'r') as f:
        sentences = f.readlines()
    
    # Perform hyperparameter tuning
    best_params = tune_hyperparameters(sentences, n_trials=50, timeout=3600)
    print(best_params)