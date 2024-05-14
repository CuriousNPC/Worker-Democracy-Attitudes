import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import os

class Agent:
    def __init__(self, node_id, archetype='learner', incubation_period=3, position=None):
        self.node_id = node_id
        self.archetype = archetype
        self.presented_attitude = 'mercenary' if archetype == 'learner' else archetype
        self.incubation_period = incubation_period
        self.current_period = 0
        # Correctly handle position assignment
        if position is None:
            self.position = (np.random.random(), np.random.random())
        else:
            self.position = position


    def move(self):
        # Increase the standard deviation to make movement more significant
        movement = np.random.normal(0, 0.05, 2)  # Adjusted from 0.01 to 0.05
        self.position = np.clip(np.add(self.position, movement), 0, 1)

    def determine_presented_attitude(self):
        if self.archetype == 'learner':
            return f'learner-{self.presented_attitude}'
        return self.presented_attitude

    def assign_color(self):
        color_map = {
            'solidarist': 'red',
            'mercenary': 'blue',
            'learner-solidarist': 'yellow',
            'learner-mercenary': 'purple'
        }
        return color_map.get(self.determine_presented_attitude(), 'gray')



def initialize_network(n, proportions):
    agents = {}
    positions = np.random.rand(n, 2)  # Create positions for all agents at once
    idx = 0
    for archetype, count in proportions.items():
        for _ in range(count):
            if idx < n:
                agents[idx] = Agent(idx, archetype=archetype, position=positions[idx])
                idx += 1
    return agents


def update_connections(agents, radius):
    G = nx.Graph()
    for agent_id, agent in agents.items():
        G.add_node(agent_id)  # This ensures all nodes are added, even if they don't have edges

    positions = np.array([agent.position for agent in agents.values()])
    for i, agent in agents.items():
        position = positions[i]
        distances = np.linalg.norm(positions - position, axis=1)
        neighbors = np.where((distances > 0) & (distances < radius))[0]
        for neighbor in neighbors:
            if neighbor != i:  # Ensure not to connect node to itself
                G.add_edge(i, neighbor)
    return G


def update_attitudes(G, agents):
    change_flag = False
    for agent in agents.values():
        if agent.archetype == 'learner':
            neighbor_ids = list(G.neighbors(agent.node_id))

            # Get attitudes of neighbors, or continue with the current attitude if isolated
            if neighbor_ids:
                neighbor_attitudes = [agents[n].determine_presented_attitude() for n in neighbor_ids]

                # Count solidarist and mercantile attitudes considering learner variants
                solidarist_count = sum(1 for att in neighbor_attitudes if 'solidarist' in att)
                mercantile_count = sum(1 for att in neighbor_attitudes if 'mercantile' in att)

                # Decision logic for switching attitudes
                if solidarist_count > (len(neighbor_attitudes) / 2):
                    new_attitude = 'solidarist'


                else:
                    new_attitude = 'mercenary'  # Maintain current attitude if no clear majority
            else:
                # If no neighbors, maintain the current attitude
                continue

            # Apply the new attitude if it's different from the current one
            if new_attitude != agent.presented_attitude:
                agent.presented_attitude = new_attitude
                agent.current_period = 0
                change_flag = True
            else:
                agent.current_period += 1

    return change_flag


def take_snapshot(G, agents, step, run_id, proportions, radius, incubation_period):
    snapshot_folder = 'snapshots'
    os.makedirs(snapshot_folder, exist_ok=True)
    proportions_str = '_'.join(f"{k}{v}" for k, v in proportions.items())
    filename = f'snapshot_r{radius}_inc{incubation_period}_{proportions_str}_run{run_id}_step{step}.png'
    file_path = os.path.join(snapshot_folder, filename)

    plt.figure(figsize=(8, 8))
    pos = {agent.node_id: agent.position for agent in agents.values() if agent.node_id in G}
    colors = [agent.assign_color() for agent in agents.values() if agent.node_id in G]
    nx.draw(G, pos, node_color=colors, with_labels=False, node_size=50)
    plt.title(f'Run {run_id} - Step {step}')
    plt.savefig(file_path)
    plt.close()

def run_simulation(simulation_steps, n, proportions, radius, incubation_period, run_id):
    agents = initialize_network(n, proportions)
    steps_for_snapshots = [0, simulation_steps // 2, simulation_steps - 1]

    for step in range(simulation_steps):
        for agent in agents.values():
            agent.move()  # Ensure agents are moved at each step
        G = update_connections(agents, radius)

        update_attitudes(G, agents)

        if step in steps_for_snapshots:
            take_snapshot(G, agents, step, run_id, proportions, radius, incubation_period)

    final_learner_attitudes = {f'learner-{attitude}': sum(1 for ag in agents.values() if ag.archetype == 'learner' and ag.determine_presented_attitude() == f'learner-{attitude}') for attitude in ['solidarist', 'mercenary']}
    return final_learner_attitudes


def main():
    simulation_steps = 100
    n = 100
    proportions_variations = [{'solidarist': 10,  'mercenary': 30, 'learner': 60},
                              {'solidarist': 20, 'mercenary': 20, 'learner': 60},
                              {'solidarist': 30, 'mercenary': 10, 'learner': 60}
                               ]
    radius_values = [0.02, 0.05, 0.10] # check whatever this is but ok for now
    incubation_periods = [1] #can add more later, already redundant actually
    repetitions = 5 # can change
    results = []

    for proportions in proportions_variations:
        for radius in radius_values:
            for incubation_period in incubation_periods:
                for rep in range(repetitions):
                    learner_attitudes = run_simulation(simulation_steps, n, proportions, radius, incubation_period, rep)
                    results.append({
                        'proportions': proportions,
                        'radius': radius,
                        'incubation_period': incubation_period,
                        'learner-solidarist': learner_attitudes.get('learner-solidarist', 0),
                        'learner-mercenary': learner_attitudes.get('learner-mercenary', 0)
                    })

    df = pd.DataFrame(results)
    df.to_excel('simulation_results.xlsx', index=False)

if __name__ == "__main__":
    main()
