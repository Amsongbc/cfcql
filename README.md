# cfcql

bayes offline phase, using Bernoulli masks dataset in src/run/run.py 298-305
bayes online phase, construct distribution in src/runners/bayes_parallel_runner.py 126-145

bayes offline trainning command:
```shell
for i in {1..5}
do
    python3 src/main.py --config=cql_qmix --env-config=sc2 with env_args.map_name=2s3z h5file_suffix=expert global_cql_alpha=50 moderate_lambda=True softmax_temp=0.5 save_model=True mask_number=$i use_bayes=True
done
```
bayes online trainning command:
```shell
python3 src/main.py --config=bayes_baseline_iql --env-config=sc2 with env_args.map_name=2s3z h5file_suffix=expert
```
