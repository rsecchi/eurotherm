# Running a single test 

```
docker exec -it devel /bin/bash
./run_leo_main.sh spool/<test_name>.cfg
```


# Running regression test

```
docker exec -it devel /bin/bash🚡
python3 regtests/run_tests.py
```


