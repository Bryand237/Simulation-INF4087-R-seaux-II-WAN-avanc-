#!/usr/bin/env python3
# Mini controleur SD-WAN : mesure 3 liens et choisit le premier qui respecte le SLA
import csv, re, subprocess, time

NS = 'agence'
LIENS = {1: '10.1.0.2', 2: '10.2.0.2', 3: '10.3.0.2'} # preference : 1, puis 2, puis 3
SLA = {'rtt_ms': 100.0, 'perte_pct': 1.0} # voix : < 100 ms et < 1 %
DEST = '10.99.0.1/32' # application au datacenter
PERIODE_S = 2


def mesure(ip):
    sortie = subprocess.run(['ip', 'netns', 'exec', NS, 'ping', '-c', '10', '-i', '0.2', '-W', '1', ip], capture_output=True, text=True).stdout
    perte_re = re.search(r'([\d.]+)% packet loss', sortie)
    perte = float(perte_re.group(1)) if perte_re else 100.0
    m = re.search(r'= [\d.]+/([\d.]+)/', sortie)
    rtt = float(m.group(1)) if m else float('inf')
    return rtt, perte


def respecte_sla(rtt, perte):
    return rtt < SLA['rtt_ms'] and perte < SLA['perte_pct']


actuel = None
with open('sla_log.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['t_s', 'lien', 'rtt_ms', 'perte_pct', 'sla_ok', 'choisi'])
    t0 = time.time()
    while True:
        mesures = {k: mesure(ip) for k, ip in LIENS.items()}
        ok = [k for k, (r, p) in mesures.items() if respecte_sla(r, p)]
        # si aucun lien ne respecte le SLA, on prend celui qui a le plus faible RTT
        choix = ok[0] if ok else min(mesures, key=lambda k: mesures[k][0])

        if choix != actuel:
            subprocess.run(['ip', '-n', NS, 'route', 'replace', DEST, 'via', LIENS[choix], 'dev', 'a%d' % choix], check=True)
            print('[%6.1fs] bascule vers le lien %d' % (time.time() - t0, choix), flush=True)
            actuel = choix

        for k, (r, p) in mesures.items():
            w.writerow([round(time.time() - t0, 1), k, r, p, int(respecte_sla(r, p)), int(k == actuel)])

        f.flush()
        time.sleep(PERIODE_S)