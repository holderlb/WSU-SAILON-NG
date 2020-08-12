# ************************************************************************************************ #
# **                                                                                            ** #
# **  AIQ-SAIL-ON TA2 Agent Class Template                                                      ** #
# **                                                                                            ** #
# **  Larry Holder, 2020                                                                        ** #
# **                                                                                            ** #
# **  Tools by the AI Lab - Artificial Intelligence Quotient (AIQ) in the School of Electrical  ** #
# **  Engineering and Computer Science at Washington State University.                          ** #
# **                                                                                            ** #
# **  Copyright Washington State University, 2020                                               ** #
# **                                                                                            ** #
# **  Contact: Brian L. Thomas (bthomas1@wsu.edu)                                               ** #
# **  Contact: Larry Holder (holder@wsu.edu)                                                    ** #
# **  Contact: Diane J. Cook (djcook@wsu.edu)                                                   ** #
# ************************************************************************************************ #

import random
import time

class TA2Agent():
    
    def __init__(self):
        #print("TA2Agent: init")
        self.possible_answers = []
        return

    def experiment_start(self):
        #print("TA2Agent: experiment_start")
        return
    
    def training_start(self):
        #print("TA2Agent: training_start")
        return
    
    def training_episode_start(self):
        #print("TA2Agent: training_episode_start")
        return
    
    def training_instance(self, feature_vector, feature_label):
        """
        Inputs:
            feature_vector: list of numbers (sensor values), real or integer
            feature_label: list of integers, one per class (one-hot for now)
        Outputs:
            label_prediction: list of integers, one per class label (one-hot for now)
            novelty_detected: Boolean (True or False) as to whether agent detects novelty
            novelty: integer representing predicted novelty level
        """
        #print("TA2Agent: training_instance")
        if feature_label not in self.possible_answers:
            self.possible_answers.append(feature_label)
        
        # Return dummy random label, but ideally label determined by incrementally trained model
        label_prediction = random.choice(self.possible_answers)
        
        novelty_detected = False # no novelty in training
        novelty = 0 # training instances are always novelty level 0
        
        return label_prediction, novelty_detected, novelty
    
    def training_performance(self, value):
        """
        value: number representing running performance (e.g., accuracy) of agent
        """
        #print("TA2Agent: training_performance")
        return
    
    def training_episode_end(self):
        #print("TA2Agent: training_episode_end")
        return
    
    def training_end(self):
        #print("TA2Agent: training_end")
        return
    
    def train_model(self):
        #print("TA2Agent: train_model")
        time.sleep(5) # simulated training
        self.save_model()
        return
    
    def save_model(self):
        """Save current trained model so agent can reset to it at the start of each trial."""
        #print("TA2Agent: save_model")
        return
    
    def reset_model(self):
        """Reset model to state just after training."""
        #print("TA2Agent: reset_model")
        return
        
    def novelty_start(self):
        #print("TA2Agent: novelty_start")
        return
    
    def trial_start(self):
        #print("TA2Agent: trial_start")
        self.reset_model()
        return
    
    def testing_start(self):
        #print("TA2Agent: testing_start")
        return
    
    def testing_episode_start(self):
        #print("TA2Agent: testing_episode_start")
        return
    
    def testing_instance(self, feature_vector, novelty_indicator):
        """
        Inputs:
            feature_vector: list of numbers (sensor values), real or integer
            novelty_indicator:
                True = novelty has been introduced
                False = novelty has not been introduced
                None = no information about novelty
        Outputs:
            label_prediction: list of integers, one per class label (one-hot for now)
            novelty_detected: Boolean (True or False) as to whether agent detects novelty
            novelty: integer representing predicted novelty level
        """
        #print("TA2Agent: testing_instance")
        
        # Return dummy random choices, but should be determined by trained model
        label_prediction = random.choice(self.possible_answers)
        novelty_detected = random.choice([True, False])
        novelty = random.choice(list(range(4)))
        
        return label_prediction, novelty_detected, novelty
    
    def testing_performance(self, value):
        """
        value: number representing running performance (e.g., accuracy) of agent
        """
        #print("TA2Agent: testing_performance")
        return
    
    def testing_episode_end(self):
        #print("TA2Agent: testing_episode_end")
        return
    
    def testing_end(self):
        #print("TA2Agent: testing_end")
        return
    
    def trial_end(self):
        #print("TA2Agent: trial_end")
        return
    
    def novelty_end(self):
        #print("TA2Agent: novelty_end")
        return
    
    def experiment_end(self):
        #print("TA2Agent: experiment_end")
        return
    