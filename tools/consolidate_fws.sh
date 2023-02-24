start_time="$(date -u +%s)"
echo "_________________________________INIT_TRY_______________________________">> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo date >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running main.py -d ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/main.py -d >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running main.py -f ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/main.py -f >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running main.py -p ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/main.py -p >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running consolidate_fws.py ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/tools/consolidate_fws.py >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running ping.py ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/tools/ping.py >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running nmap.py ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/tools/nmap.py >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running ssh.py ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/tools/ssh.py >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "|||||||||||||||||||||||||||| Running fortigate_api.py ||||||||||||||||||||||||" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
python3 /home/ahenao/net-discovery/tools/fortigate_api.py >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
end_time="$(date -u +%s)"
elapsed="$(($end_time-$start_time))"
echo "Total of $elapsed seconds elapsed for process" >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo date >> /home/ahenao/net-discovery/logs/consolidate.out 2>&1
echo "_________________________________END_TRY_________________________________">> /home/ahenao/net-discovery/logs/consolidate.out 2>&1