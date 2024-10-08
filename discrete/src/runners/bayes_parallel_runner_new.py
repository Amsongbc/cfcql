from envs import REGISTRY as env_REGISTRY
from functools import partial
from components.episode_buffer import EpisodeBatch
from multiprocessing import Pipe, Process
import numpy as np
import torch as th
import os
# Based (very) heavily on SubprocVecEnv from OpenAI Baselines
# https://github.com/openai/baselines/blob/master/baselines/common/vec_env/subproc_vec_env.py
class BayesParallelRunnerNew:

    def __init__(self, args, logger):
        self.args = args
        self.logger = logger
        self.batch_size = self.args.batch_size_run

        # Make subprocesses for the envs
        self.parent_conns, self.worker_conns = zip(*[Pipe() for _ in range(self.batch_size)])
        env_fn = env_REGISTRY[self.args.env]
        self.ps = []

        for i, worker_conn in enumerate(self.worker_conns):
            ps = Process(target=env_worker, 
                    args=(worker_conn, CloudpickleWrapper(partial(env_fn, **self.args.env_args))))
            self.ps.append(ps)

        for p in self.ps:
            p.daemon = True
            p.start()

        self.parent_conns[0].send(("get_env_info", None))
        self.env_info = self.parent_conns[0].recv()
        self.episode_limit = self.env_info["episode_limit"]

        self.t = 0

        self.t_env = 0

        self.train_returns = []
        self.test_returns = []
        self.train_stats = {}
        self.test_stats = {}

        self.log_train_stats_t = -100000

    def setup(self, scheme, groups, preprocess, mac, macs,mixers, args, opponents=None):
        self.new_batch = partial(EpisodeBatch, scheme, groups, self.batch_size, self.episode_limit + 1,
                                 preprocess=preprocess, device=self.args.device)
        self.mac = mac
        self.macs=macs
        self.mixers = mixers
        self.scheme = scheme
        self.groups = groups
        self.preprocess = preprocess
        self.args=args

        if opponents is not None:
            self.opponents = opponents

    def get_env_info(self):
        return self.env_info

    def save_replay(self):
        pass

    def close_env(self):
        for parent_conn in self.parent_conns:
            parent_conn.send(("close", None))

    def reset(self):
        self.batch = self.new_batch()

        # Reset the envs
        for parent_conn in self.parent_conns:
            parent_conn.send(("reset", None))

        pre_transition_data = {
            "state": [],
            "avail_actions": [],
            "obs": []
        }
        # Get the obs, state and avail_actions back
        for parent_conn in self.parent_conns:
            data = parent_conn.recv()
            pre_transition_data["state"].append(data["state"])
            pre_transition_data["avail_actions"].append(data["avail_actions"])
            pre_transition_data["obs"].append(data["obs"])

        self.batch.update(pre_transition_data, ts=0)

        self.t = 0
        self.env_steps_this_run = 0

    def save_data(self,data):
        first_batch_data = data[0, :]  # 形状为 [agent_number]
        # output_folder="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/Q_values4"
        output_folder=os.path.join("/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/Q",self.args.unique_token)
        os.makedirs(output_folder, exist_ok=True)
        # 将每个 agent 的数据存储到单独的文件中
        for agent_idx in range(len(self.macs)):
            agent_data = first_batch_data[agent_idx]  # 获取第 agent_idx 个智能体的数据
            filename = f'agent_{agent_idx}_data.txt'  # 为每个 agent 创建一个文件名
            filepath = os.path.join(output_folder, filename)
            with open(filepath, 'a') as f:  # 'a' 模式表示追加内容
                f.write(str(agent_data) + '\n')

    def save_data_prob(self,data):
        # output_folder="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/Q_values4"
        output_folder=os.path.join("/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/prob",self.args.unique_token)
        os.makedirs(output_folder, exist_ok=True)
        # 将每个 agent 的数据存储到单独的文件中
        for agent_idx in range(len(self.macs)):
            agent_data = data[0][agent_idx]  # 获取第 agent_idx 个智能体的数据
            filename = f'agent_{agent_idx}_data.txt'  # 为每个 agent 创建一个文件名
            filepath = os.path.join(output_folder, filename)
            with open(filepath, 'a') as f:  # 'a' 模式表示追加内容
                f.write(str(agent_data) + '\n')


    def run(self, test_mode=False):
        self.reset()

        all_terminated = False
        episode_returns = [0 for _ in range(self.batch_size)]
        episode_lengths = [0 for _ in range(self.batch_size)]
        self.mac.init_hidden(batch_size=self.batch_size)
        for i in range(len(self.macs)):
            self.macs[i].init_hidden(batch_size=self.batch_size)
        terminated = [False for _ in range(self.batch_size)]
        envs_not_terminated = [b_idx for b_idx, termed in enumerate(terminated) if not termed]
        final_env_infos = []  # may store extra stats like battle won. this is filled in ORDER OF TERMINATION
        
        save_probs = getattr(self.args, "save_probs", False)
        while True:

            # Pass the entire batch of experiences up till now to the agents
            # Receive the actions for each agent at this timestep in a batch for each un-terminated env
            if save_probs:
                actions, probs = self.mac.select_actions(self.batch, t_ep=self.t, t_env=self.t_env, bs=envs_not_terminated, test_mode=test_mode)
            else:
                #Use multiple macs, and then use bayes to select a selection action from these macs
                if self.args.use_bayes:
                    q_outs=[]
                    actions_list=[]
                    for i in range(len(self.macs)):
                        actions = self.mac.select_actions(self.batch, t_ep=self.t, t_env=self.t_env,
                                                          bs=envs_not_terminated,
                                                          test_mode=test_mode)
                        actions, qvals = self.macs[i].get_Q(self.batch, t_ep=self.t, t_env=self.t_env, bs=envs_not_terminated, test_mode=test_mode,get_Q=True)
                        qvals_expanded = qvals.unsqueeze(1)
                        state_expanded=self.batch["state"][envs_not_terminated, self.t]

                        qtotals = self.mixers[i](qvals_expanded, state_expanded)
                        qtotals=qtotals.squeeze(1)
                        q_outs.append(qtotals)
                        actions_list.append(actions)

                    q_outs = th.cat(q_outs, dim=1)
                    mac_probs = th.nn.functional.softmax(q_outs, dim=1)
                    selected_mac_idx = th.multinomial(mac_probs, num_samples=1).squeeze(1)
                    actions = th.stack([actions_list[i][b] for b, i in enumerate(selected_mac_idx)], dim=0)

                    if test_mode==False:
                        self.save_data_prob(mac_probs)
                        self.save_data(q_outs)
                else:
                    actions = self.mac.select_actions(self.batch, t_ep=self.t, t_env=self.t_env, bs=envs_not_terminated,
                                                      test_mode=test_mode)

            cpu_actions = actions.to("cpu").numpy()

            # Update the actions taken
            actions_chosen = {
                "actions": actions.unsqueeze(1).to("cpu"),
            }
            if save_probs:
                actions_chosen["probs"] = probs.unsqueeze(1).to("cpu")
            
            self.batch.update(actions_chosen, bs=envs_not_terminated, ts=self.t, mark_filled=False)
            
            # Send actions to each env
            action_idx = 0
            for idx, parent_conn in enumerate(self.parent_conns):
                if idx in envs_not_terminated: # We produced actions for this env
                    if not terminated[idx]: # Only send the actions to the env if it hasn't terminated
                        parent_conn.send(("step", cpu_actions[action_idx]))
                    action_idx += 1 # actions is not a list over every env

            # Update envs_not_terminated
            envs_not_terminated = [b_idx for b_idx, termed in enumerate(terminated) if not termed]
            all_terminated = all(terminated)
            if all_terminated:
                break

            # Post step data we will insert for the current timestep
            post_transition_data = {
                "reward": [],
                "terminated": []
            }
            # Data for the next step we will insert in order to select an action
            pre_transition_data = {
                "state": [],
                "avail_actions": [],
                "obs": []
            }
            # Receive data back for each unterminated env
            for idx, parent_conn in enumerate(self.parent_conns):
                if not terminated[idx]:
                    data = parent_conn.recv()
                    # Remaining data for this current timestep
                    post_transition_data["reward"].append((data["reward"],))

                    episode_returns[idx] += data["reward"]
                    episode_lengths[idx] += 1
                    if not test_mode:
                        self.env_steps_this_run += 1

                    env_terminated = False
                    if data["terminated"]:
                        final_env_infos.append(data["info"])
                    if data["terminated"] and not data["info"].get("episode_limit", False):
                        env_terminated = True
                    terminated[idx] = data["terminated"]
                    post_transition_data["terminated"].append((env_terminated,))

                    # Data for the next timestep needed to select an action
                    pre_transition_data["state"].append(data["state"])
                    pre_transition_data["avail_actions"].append(data["avail_actions"])
                    pre_transition_data["obs"].append(data["obs"])

            # Add post_transiton data into the batch
            self.batch.update(post_transition_data, bs=envs_not_terminated, ts=self.t, mark_filled=False)

            # Move onto the next timestep
            self.t += 1

            # Add the pre-transition data
            self.batch.update(pre_transition_data, bs=envs_not_terminated, ts=self.t, mark_filled=True)

        if not test_mode:
            self.t_env += self.env_steps_this_run

        # Get stats back for each env
        for parent_conn in self.parent_conns:
            parent_conn.send(("get_stats",None))

        env_stats = []
        for parent_conn in self.parent_conns:
            env_stat = parent_conn.recv()
            env_stats.append(env_stat)

        cur_stats = self.test_stats if test_mode else self.train_stats
        cur_returns = self.test_returns if test_mode else self.train_returns
        log_prefix = "test_" if test_mode else ""
        if self.args.test_nepisode > 50:
            log_prefix = "final_" + log_prefix 
        infos = [cur_stats] + final_env_infos

        # if test_mode:
        #     print(infos)
        #     print(set.union(*[set(d) for d in infos]))
        #     for d in infos:
        #         print(d.get('success',0))
        #     print(sum(d.get('success', 0) for d in infos))


        cur_stats.update({k: sum(d.get(k, 0) for d in infos) for k in set.union(*[set(d) for d in infos])})
        cur_stats["n_episodes"] = self.batch_size + cur_stats.get("n_episodes", 0)
        cur_stats["ep_length"] = sum(episode_lengths) + cur_stats.get("ep_length", 0)

        cur_returns.extend(episode_returns)

        n_test_runs = max(1, self.args.test_nepisode // self.batch_size) * self.batch_size
        if test_mode and (len(self.test_returns) == n_test_runs):
            # print(cur_stats)
            self._log(cur_returns, cur_stats, log_prefix)
        elif self.t_env - self.log_train_stats_t >= self.args.runner_log_interval:
            self._log(cur_returns, cur_stats, log_prefix)
            # if hasattr(self.mac.action_selector, "epsilon"):
            #     self.logger.log_stat("epsilon", self.mac.action_selector.epsilon, self.t_env)
            if hasattr(self.macs[0].action_selector, "epsilon"):
                self.logger.log_stat("epsilon", self.macs[0].action_selector.epsilon, self.t_env)
            self.log_train_stats_t = self.t_env

        return self.batch

    def _log(self, returns, stats, prefix):
        if 'final' in prefix and stats["n_episodes"]<50:
            return
        t_env = min(self.t_env,self.args.t_max)
        self.logger.log_stat(prefix + "return_mean", np.mean(returns), t_env)
        self.logger.log_stat(prefix + "return_std", np.std(returns), t_env)
        returns.clear()

        for k, v in stats.items():
            if k != "n_episodes":
                # print(k,v)
                self.logger.log_stat(prefix + k + "_mean", v / stats["n_episodes"], t_env)

            else:
                self.logger.log_stat(prefix + k , v, t_env)
        stats.clear()


def env_worker(remote, env_fn):
    # Make environment
    env = env_fn.x()
    while True:
        cmd, data = remote.recv()
        if cmd == "step":
            actions = data
            # Take a step in the environment
            reward, terminated, env_info = env.step(actions)
            # Return the observations, avail_actions and state to make the next action
            state = env.get_state()
            avail_actions = env.get_avail_actions()
            obs = env.get_obs()
            remote.send({
                # Data for the next timestep needed to pick an action
                "state": state,
                "avail_actions": avail_actions,
                "obs": obs,
                # Rest of the data for the current timestep
                "reward": reward,
                "terminated": terminated,
                "info": env_info
            })
        elif cmd == "reset":
            env.reset()
            remote.send({
                "state": env.get_state(),
                "avail_actions": env.get_avail_actions(),
                "obs": env.get_obs()
            })
        elif cmd == "close":
            env.close()
            remote.close()
            break
        elif cmd == "get_env_info":
            remote.send(env.get_env_info())
        elif cmd == "get_stats":
            remote.send(env.get_stats())
        else:
            raise NotImplementedError


class CloudpickleWrapper():
    """
    Uses cloudpickle to serialize contents (otherwise multiprocessing tries to use pickle)
    """
    def __init__(self, x):
        self.x = x
    def __getstate__(self):
        import cloudpickle
        return cloudpickle.dumps(self.x)
    def __setstate__(self, ob):
        import pickle
        self.x = pickle.loads(ob)

