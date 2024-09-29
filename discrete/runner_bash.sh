#!/bin/bash

#!/bin/bash


for i in {1..5}
do
    # Run the Python command with the current mask_number
    python3 src/main.py --config=cql_qmix --env-config=sc2 with env_args.map_name=6h_vs_8z h5file_suffix=expert global_cql_alpha=50 moderate_lambda=True softmax_temp=0 save_model=True mask_number=$i use_bayes=True
done
for i in {1..5}
do
    # Run the Python command with the current mask_number
    python3 src/main.py --config=cql_qmix --env-config=sc2 with env_args.map_name=6h_vs_8z h5file_suffix=mixed global_cql_alpha=50 moderate_lambda=True softmax_temp=1 save_model=True mask_number=$i use_bayes=True
done

##python3 src/main.py --config=cql_qmix_online --env-config=sc2 with env_args.map_name=3s_vs_5z  h5file_suffix=medium_replay global_cql_alpha=50  moderate_lambda=True softmax_temp=0 save_model=True checkpoint_path="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/models/3s_vs_5z/slsoftmaxkl_0_5000_cql_qmix_env=8_adam_td_lambda__3s_vs_5z__medium_replay_global_cql_alpha_50___parallel__2024-08-27_01-09-22"
##python3 src/main.py --config=cql_qmix_online --env-config=sc2 with env_args.map_name=6h_vs_8z  h5file_suffix=expert global_cql_alpha=50  moderate_lambda=True softmax_temp=0 checkpoint_path="/root/autodl-tmp/discrete/results/models/6h_vs_8z/slsoftmaxkl_0_5000_cql_qmix_env=8_adam_td_lambda__6h_vs_8z__expert_global_cql_alpha_50___parallel__2024-08-27_22-14-06"
##
##python3 src/main.py --config=cql_qmix_online --env-config=sc2 with env_args.map_name=6h_vs_8z  h5file_suffix=mixed global_cql_alpha=50  moderate_lambda=True softmax_temp=1 save_model=True checkpoint_path="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/models/6h_vs_8z/slsoftmaxkl_1_5000_cql_qmix_env=8_adam_td_lambda__6h_vs_8z__mixed_global_cql_alpha_50___parallel__2024-08-27_23-04-05"
#
##python3 src/main.py --config=qmix_online --env-config=sc2 with env_args.map_name=6h_vs_8z  h5file_suffix=expert save_model=True checkpoint_path="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/models/6h_vs_8z/slsoftmaxkl_0_5000_cql_qmix_env=8_adam_td_lambda__6h_vs_8z__expert_global_cql_alpha_50___parallel__2024-08-27_22-14-06"
##
##python3 src/main.py --config=qmix_online --env-config=sc2 with env_args.map_name=6h_vs_8z  h5file_suffix=mixed save_model=True checkpoint_path="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/models/6h_vs_8z/slsoftmaxkl_1_5000_cql_qmix_env=8_adam_td_lambda__6h_vs_8z__mixed_global_cql_alpha_50___parallel__2024-08-27_23-04-05"
#
#python3 src/main.py --config=baseline_iql_online --env-config=sc2 with env_args.map_name=6h_vs_8z  h5file_suffix=expert save_model=True checkpoint_path="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/models/6h_vs_8z/slsoftmaxkl_0_5000_cql_qmix_env=8_adam_td_lambda__6h_vs_8z__expert_global_cql_alpha_50___parallel__2024-08-27_22-14-06"
#
#python3 src/main.py --config=baseline_iql_online --env-config=sc2 with env_args.map_name=6h_vs_8z  h5file_suffix=mixed save_model=True checkpoint_path="/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/models/6h_vs_8z/slsoftmaxkl_1_5000_cql_qmix_env=8_adam_td_lambda__6h_vs_8z__mixed_global_cql_alpha_50___parallel__2024-08-27_23-04-05"
#
#python3 src/main.py --config=bayes_baseline_iql --env-config=sc2 with env_args.map_name=3s_vs_5z h5file_suffix=expert

