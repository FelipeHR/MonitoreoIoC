import subprocess
subprocess.run("nohup python3 Loki-0.45.0/loki.py --onlyrelevant -l log.txt &", shell = True, check = True)