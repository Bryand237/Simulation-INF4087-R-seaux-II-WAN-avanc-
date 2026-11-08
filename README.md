# Réseaux II (WAN avancé) — Simulations et laboratoires

> **INF4087 Réseaux II** · Master 1 Recherche · Groupe de 4 étudiants
> Ce dépôt contient les bancs de simulation, les scripts, les mesures brutes et le journal de laboratoire qui accompagnent le cours. Méthode commune aux 8 parties du syllabus ; **Partie 1 détaillée**, parties 2 à 8 à compléter une par une sur la même trame.

Le but n'est pas de « faire tourner un réseau » mais de **comprendre une notion du cours en la mesurant** : chaque laboratoire pose une question mesurable, monte un banc scripté, fait varier un seul paramètre, puis conclut en disant aussi ce que le banc ne reproduit pas.

## Sommaire

1. [Démarrage rapide](#1-démarrage-rapide)
2. [Organisation du dépôt](#2-organisation-du-dépôt)
3. [Les laboratoires de la Partie 1](#3-les-laboratoires-de-la-partie-1)
4. [Poste de travail et outils](#4-poste-de-travail-et-outils)
5. [Méthode commune](#5-méthode-commune)
6. [Feuille de route des parties 2 à 8](#6-feuille-de-route-des-parties-2-à-8)
7. [Travailler en groupe](#7-travailler-en-groupe)
8. [Statuts et limites](#8-statuts-et-limites)
9. [Normes de référence](#9-normes-de-référence)
10. [Équipe](#10-équipe)

---

## 1. Démarrage rapide

Dix commandes pour récupérer le dépôt, monter le banc de base de la Partie 1 et rejouer le lab 1.1. Poste Linux, droits `sudo` ; le détail de chaque étape est dans le README du lab.

```bash
git clone <URL-DU-DÉPÔT> reseaux2-sim && cd reseaux2-sim/partie1     # 1. récupérer le dépôt
sudo modprobe sch_netem && echo netem OK                              # 2. l'émulateur de liens est-il disponible ?
sudo bash 01_base.sh                                                  # 3. monter le banc : agence, datacenter, 3 liens
sudo ip netns exec agence ping -c 5 10.1.0.2                          # 4. contrôler : RTT proche de 20 ms
cd lab1_1_sdwan                                                       # 5. entrer dans le lab 1.1
sudo python3 sla_controller.py                                        # 6. (terminal A) lancer le contrôleur SD-WAN
sudo ip netns exec agence ping -D -i 0.2 10.99.0.1 | tee ping_app.log # 7. (terminal B) trafic témoin
sudo ip netns exec agence tc qdisc change dev a1 root netem delay 120ms loss 5% rate 20mbit   # 8. dégrader le lien 1 (côté agence)…
sudo ip netns exec dc     tc qdisc change dev d1 root netem delay 120ms loss 5% rate 20mbit   # 9. … et côté datacenter : observer la bascule
sudo bash ../99_nettoyage.sh                                          # 10. nettoyer (après Ctrl+C dans les deux terminaux)
```

Remplacer `<URL-DU-DÉPÔT>` par l'adresse du dépôt. Si `modprobe sch_netem` échoue, le noyau n'a pas `netem` : passer sur une machine virtuelle Linux standard (cas à tester notamment sous WSL2). À la fin de chaque séance, vérifier que le banc est bien supprimé (voir § 4).

> Le détail de la procédure, les mesures à relever et l'analyse se trouvent dans [`partie1/lab1_1_sdwan/README.md`](partie1/lab1_1_sdwan/README.md).

---

## 2. Organisation du dépôt

```
reseaux2-sim/
├── README.md              # ce document : comment tout reproduire en 10 commandes
├── journal/               # un fichier daté par séance
├── partie1/               # Fondamentaux WAN modernes (diapositives 3 à 7)
│   ├── 01_base.sh         # banc de base : une agence, un datacenter, trois liens
│   ├── 99_nettoyage.sh    # supprime le banc en fin de séance
│   ├── lab1_1_sdwan/      # De la ligne louée au mini-SD-WAN
│   ├── lab1_2_quic/       # QUIC contre TCP
│   ├── lab1_3_pppoe/      # PPP et PPPoE
│   ├── lab1_4_icmp/       # ICMP et PMTUD
│   ├── lab1_5_nat64/      # IPv6-only et NAT64
│   ├── lab1_6_lso/        # API MEF LSO en maquette
│   ├── resultats/         # CSV bruts, jamais modifiés à la main
│   └── figures/           # graphiques produits à partir de resultats/
└── partie2/ … partie8/    # mêmes sous-dossiers, ajoutés au fur et à mesure
```

| Dossier | Contenu | Règle |
|---|---|---|
| `partieN/lab…/` | scripts du lab, `README.md` du lab | tout est scripté : **aucun clic non reproductible** |
| `partie1/resultats/` | mesures brutes (CSV) | jamais modifiées à la main ; versionnées avec le script d'analyse |
| `partie1/figures/` | graphiques | régénérables à partir de `resultats/` |
| `journal/` | un fichier par séance | date, objectif, commandes, versions, résultats, écarts |

Chaque lab a son propre `README.md` : objectif, hypothèse, topologie, procédure, mesures, analyse, limites.

---

## 3. Les laboratoires de la Partie 1

La Partie 1 couvre les fondamentaux du WAN moderne : pourquoi remplacer une ligne louée unique par plusieurs transports pilotés par un contrôleur (SD-WAN), ce que QUIC change par rapport à TCP, le rôle de PPP, PPPoE et ICMP, puis IPv6-only, NAT64 et l'API MEF LSO.

| Lab | Dossier | Ce qu'on veut comprendre | Diapositives | Outils probables | README | Statut |
|---|---|---|---|---|---|---|
| 1.1 | `lab1_1_sdwan/` | Politique SLA d'un SD-WAN : mesurer plusieurs liens, choisir celui qui respecte le seuil (RTT < 100 ms, perte < 1 %), basculer quand il se dégrade | 3–4 (SLA : 29) | espaces de noms, `netem`, Python | [lien](partie1/lab1_1_sdwan/README.md) | À tester |
| 1.2 | `lab1_2_quic/` | QUIC contre TCP (exemple d'hypothèse du guide : QUIC termine plus vite que TCP quand la perte dépasse 1 %) | 5 | `netem`, nginx HTTP/3, `curl`, `qperf` | à rédiger | À documenter |
| 1.3 | `lab1_3_pppoe/` | PPP et PPPoE | 6 | `pppd` | à rédiger | À documenter |
| 1.4 | `lab1_4_icmp/` | Rôle d'ICMP et PMTUD (découverte de la MTU du chemin) | 6 | à définir | à rédiger | À documenter |
| 1.5 | `lab1_5_nat64/` | IPv6-only et NAT64 | 7 | espaces de noms, Jool | à rédiger | À documenter |
| 1.6 | `lab1_6_lso/` | API MEF LSO en maquette | 7 | à définir | à rédiger | À documenter |

*« À tester » : script contrôlé pour la syntaxe, jamais exécuté par l'auteur du guide ; le groupe doit le lancer et noter les écarts. « À documenter » : dossier à remplir sur la même trame que le lab 1.1. Les outils des labs 1.2 à 1.6 sont déduits de la liste des outils de la Partie 1 du guide (§ 6 ci-dessous) : à confirmer lab par lab.*

**Points d'observation relevés dans le rapport sur la Partie 1** (à garder en tête pendant les labs) :

- QUIC n'est pas un acronyme ;
- le RFC 8781 n'est pas NAT64 ;
- le syllabus place PPP sur FRR alors que la liste des protocoles de FRR n'en contient pas : on utilise donc `pppd`.

---

## 4. Poste de travail et outils

### Deux profils

- **Léger** : Linux seul, Docker uniquement si Containerlab est utilisé (la documentation consultée cite Ubuntu 20.04+ ou Debian 11+).
- **Complet** : GNS3 avec sa machine virtuelle (4 Go de mémoire libre recommandés, 20 Go de disque, virtualisation matérielle).

La Partie 1 utilise le profil léger.

### Vérifier le poste avant toute chose

```bash
uname -r                                          # version du noyau
ip -V                                             # iproute2 présent ?
tc -V                                             # outil tc présent ?
sudo modprobe sch_netem && echo netem OK          # émulateur de liens disponible ?
docker --version                                  # seulement pour Containerlab
```

### Choisir l'outil

| Outil | À utiliser quand | Limites |
|---|---|---|
| Espaces de noms Linux + `veth` + `netem` | comprendre un protocole sur un lien dégradé (QUIC/TCP, ICMP, PPPoE, NAT64) ; **léger** | pas d'interface graphique ; `netem` agit en sortie ; droits root |
| Containerlab + FRR | topologies de routeurs (OSPF, BGP, PIM, LDP…) décrites dans un fichier YAML | pas d'interface graphique ; Linux requis ; Docker |
| GNS3 | images d'équipements réels, topologie graphique | images à obtenir soi-même ; plus lourd |
| EVE-NG, ns-3 | serveur dédié (EVE-NG) ; simulation à événements discrets, grandes échelles (ns-3) | non étudiés ici |

**Émulation ou simulation ?** L'émulation exécute de vrais logiciels (pile TCP/IP de Linux, FRR, nginx) sur des liens artificiels : le comportement des protocoles est proche du réel, mais l'émulateur de liens a ses limites, par exemple la granularité de l'horloge du noyau, qui peut perturber débit et délai. La simulation à événements discrets (ns-3) modélise le réseau mathématiquement ; elle n'est pas étudiée ici.

### Nettoyer le banc

À la fin de chaque séance :

```bash
sudo bash partie1/99_nettoyage.sh
# à la main, pour le banc de base, si le script n'est pas disponible :
sudo ip netns del agence ; sudo ip netns del dc
```

Si `ip netns add` répond « File exists » au lancement suivant, un banc précédent n'a pas été nettoyé.

---

## 5. Méthode commune

Chaque laboratoire suit le même processus en 7 étapes :

| Étape | Action | Livrable |
|---|---|---|
| 1. Question | Écrire une question mesurable et une hypothèse | Fiche de question |
| 2. Outil | Choisir l'outil (§ 4) | Choix justifié |
| 3. Topologie | Dessiner, adresser, lister les liens et leurs paramètres | Schéma + tableau d'adressage |
| 4. Construction | Scripter chaque commande (aucun clic non reproductible) et versionner | Scripts dans Git |
| 5. Expériences | Fixer variables, valeurs, répétitions, durée, graine | Plan d'expériences |
| 6. Analyse | Collecter (CSV, pcap), calculer médiane et dispersion, tracer | Tableaux et graphiques |
| 7. Rapport | Conclure, lister les limites, relier aux normes (RFC) | Rapport + dépôt |

**Règle d'or :** un banc de simulation répond à une question précise ; il ne prouve pas que le réseau réel se comporte pareil. Chaque rapport dit donc ce que le banc ne reproduit pas.

### Hygiène expérimentale

- Un seul paramètre change à la fois.
- Au moins **10 répétitions** par condition ; reporter la médiane et une dispersion (écart-type ou quartiles).
- Faire un tour à vide avant de mesurer et ignorer la première mesure.
- Fixer la graine quand l'outil le permet (`netem` offre l'option `seed` ; disponibilité selon la version d'iproute2 : à vérifier).
- Capturer (pcap) pour comprendre, pas pour tout stocker.
- Noter la version de chaque logiciel et la commande exacte.
- Contrôler que le banc est sain avant chaque série (`ping` des liens, `tc qdisc show`).
- Ne jamais conclure sur une seule exécution.

---

## 6. Feuille de route des parties 2 à 8

Les parties suivantes reprennent la même trame (§ 5) et le même schéma de dossiers. Le tableau donne les outils pressentis ; il sera précisé partie par partie.

| Partie (diapositives) | Thème | Outils probables | État |
|---|---|---|---|
| 1 (3–7) | Fondamentaux WAN : liens hybrides et SLA, QUIC contre TCP, PPPoE, ICMP et PMTUD, NAT64, API LSO | espaces de noms, `netem`, nginx HTTP/3, `curl`, `qperf`, `pppd`, Jool | détaillée dans ce dépôt |
| 2 (8–11) | Multicast : IGMPv3, arbres RPT et SPT, MSDP, mVPN, BIER | Containerlab + FRR (PIM-SM, MSDP) | à détailler ; BIER : alternative à chercher |
| 3 (12–14) | NAT et IPv6 : NAT44 et PAT, CGNAT, NAT64 et DNS64, MAP, 464XLAT | espaces de noms, nftables, Jool | partiellement couverte par le lab 1.5 |
| 4 (15–18) | VPN et MPLS : IPsec, LDP, L3VPN, DMVPN, SR-MPLS et SRv6 | Containerlab ou GNS3 + FRR | L3VPN et SR dans FRR : à vérifier |
| 5 (19–22) | Supervision et eBPF : SNMPv3 contre NETCONF et gNMI, eBPF et XDP, télémétrie | Prometheus, Grafana, ePPing | à détailler |
| 6 (23–26) | Performance, TE, QUIC : SR-TE et FlexAlgo, H-QoS, contrôle de congestion | iperf3, `qperf`, `tc` et `netem` | partiellement couverte par le lab 1.2 |
| 7 (27–31) | SD-WAN et SASE : contrôleur et edge, SLA par BFD, DIA, ZTNA | mini-contrôleur (lab 1.1), FRR (BFD) ; vManage 20.12 et FortiManager 7.4 cités par le syllabus | accès aux images et licences : à vérifier |
| 8 (32–37) | IA pour WAN autonome : AIOps, jumeau numérique, détection d'anomalies, Green WAN | GNS3 ou EVE-NG, Batfish, SuzieQ, Python | à détailler et vérifier |

---

## 7. Travailler en groupe

### Git

- **Une branche par étudiant**, par exemple `prenom/lab1_2_quic`.
- **Relecture croisée** avant fusion dans `main` (pull request relue par un autre membre).
- **Messages de commit descriptifs**, au format `type(portée): résumé à l'impératif`, par exemple :

  ```
  feat(lab1_1): ajouter le contrôleur SLA
  fix(base): corriger le profil netem du lien 3
  docs(lab1_1): décrire la procédure et les mesures
  chore(partie1): ajouter les mesures brutes du lab 1.1
  ```

- **Déposer les résultats bruts avec le script d'analyse**, pas seulement les graphiques : un résultat doit pouvoir se refaire.
- **Ne pas versionner** les fichiers volumineux ou régénérables : captures `.pcap` volumineuses, `__pycache__/`, environnements virtuels. Les CSV bruts, eux, **sont versionnés** (`partie1/resultats/`).

`.gitignore` de départ :

```
__pycache__/
*.pyc
.venv/
*.pcap
.env
```

### Journal de laboratoire

Un fichier daté par séance dans `journal/`, par exemple `journal/2026-11-10.md` :

```markdown
# Séance du 2026-11-10 — lab 1.1

- **Objectif :** …
- **Commandes lancées :** …
- **Versions :** noyau, iproute2, tc, Python
- **Résultats :** …
- **Écarts constatés par rapport au guide :** …
```

Les écarts par rapport au guide (une commande qui échoue, une valeur différente) sont des résultats : ils se notent, ils ne se cachent pas.

---

## 8. Statuts et limites

Trois statuts reviennent dans le dépôt :

| Statut | Signification |
|---|---|
| **Vérifié** | confirmé dans une source consultée |
| **À tester** | commande non exécutée par l'auteur du guide : à lancer par le groupe |
| **À vérifier** | point non confirmé |

Les scripts du guide ont été contrôlés pour la syntaxe (`bash -n`, `py_compile`) et l'analyse de la sortie de `ping` a été testée sur des exemples, mais **aucune commande réseau n'a été exécutée** dans l'environnement de rédaction (les outils `ip` et `tc` y sont absents). **Chaque laboratoire doit donc être exécuté par le groupe**, et les écarts notés dans le journal.

Les profils de liens (délais, pertes, débits) sont des **valeurs d'illustration**, pas des mesures d'un réseau réel.

---

## 9. Normes de référence

La Partie 1 mobilise les RFC suivants, cités dans chaque lab.

| RFC | Sujet |
|---|---|
| 9000 | QUIC : protocole de transport |
| 9114 | HTTP/3 |
| 1661 | PPP (Point-to-Point Protocol) |
| 2516 | PPPoE (PPP sur Ethernet) |
| 792 | ICMP |
| 4443 | ICMPv6 |
| 8201 | Découverte de la MTU du chemin pour IPv6 (PMTUD) |
| 6146 | NAT64 avec états |
| 8781 | Option PREF64 dans les annonces de routeur (et non NAT64 lui-même) |

---

*Encadrement, calendrier (6 semaines) et grille d'auto-évaluation du projet de groupe : à ajouter ici.*

---

*Document de référence : Guide de simulation — INF4087 Réseaux II (WAN avancé), version du 5 novembre 2026.*
