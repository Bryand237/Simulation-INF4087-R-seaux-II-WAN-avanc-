# Lab 1.1 — De la ligne louée au mini-SD-WAN

> INF4087 Réseaux II (WAN avancé) · Partie 1 — Fondamentaux WAN modernes
> Banc d'émulation : espaces de noms Linux + `veth` + `netem` · Python 3 (bibliothèque standard uniquement)

Ce laboratoire émule une agence reliée à un datacenter par **trois liens de qualité différente** (ligne louée MPLS, Internet, 5G) et un **mini-contrôleur SD-WAN** qui mesure ces liens, choisit le premier qui respecte le SLA voix, et bascule le trafic quand il se dégrade.

| | |
|---|---|
| **Objectif** | Comprendre la politique SLA d'un SD-WAN (diapositives 4 et 29 du syllabus) : mesurer plusieurs liens, choisir celui qui respecte le seuil, basculer quand il se dégrade. |
| **Hypothèse H1** | Un contrôleur qui mesure les liens et bascule le trafic maintient le SLA voix (RTT < 100 ms et perte < 1 %) là où un lien unique le violerait. |
| **Auteurs** | À compléter (noms du groupe) |
| **Date des essais** | À compléter |

---

## 1. Topologie

```
  espace de noms « agence »                         espace de noms « dc »

       a1 ============== lien 1 « ligne louée / MPLS » ============== d1
                          10 ms par sens, 0 %, 20 Mbit/s
       a2 ============== lien 2 « Internet » ====================== d2
                          20 ms ± 5 ms par sens, 0,5 %, 50 Mbit/s
       a3 ============== lien 3 « 5G » ============================ d3
                          30 ms ± 15 ms par sens, 1 %, 30 Mbit/s

                                         application : 10.99.0.1/32 (sur lo, côté dc)
```

| Lien | Réseau | Agence | Datacenter | Profil appliqué dans chaque sens | RTT attendu | Perte aller-retour | Débit |
|---|---|---|---|---|---|---|---|
| 1 (MPLS) | 10.1.0.0/24 | .1 (`a1`) | .2 (`d1`) | délai 10 ms, perte 0 % | ≈ 20 ms | 0 % | 20 Mbit/s |
| 2 (Internet) | 10.2.0.0/24 | .1 (`a2`) | .2 (`d2`) | délai 20 ms ± 5 ms, perte 0,5 % | ≈ 40 ms ± 10 | ≈ 1 % | 50 Mbit/s |
| 3 (5G) | 10.3.0.0/24 | .1 (`a3`) | .2 (`d3`) | délai 30 ms ± 15 ms, perte 1 % | ≈ 60 ms ± 30 | ≈ 2 % | 30 Mbit/s |

Le profil est appliqué **dans chaque sens** (`netem` agit en sortie, donc des deux côtés du lien) : le RTT vaut deux fois le délai, et la perte aller-retour environ le double. Ces profils sont des valeurs d'illustration choisies pour le guide, pas des mesures d'un réseau réel.

**Politique du contrôleur :** préférence au lien 1, puis 2, puis 3 ; un lien respecte le SLA si `RTT < 100 ms` **et** `perte < 1 %`.

---

## 2. Prérequis

Poste Linux avec les droits `root` (ou `sudo`). Aucune dépendance à installer : Docker n'est pas nécessaire pour ce lab.

Vérification du poste :

```bash
uname -r                                          # version du noyau
ip -V                                             # iproute2 présent ?
tc -V                                             # outil tc présent ?
sudo modprobe sch_netem && echo netem OK          # émulateur de liens disponible ?
python3 --version                                 # Python 3 requis
```

Si `modprobe sch_netem` échoue, le noyau n'a pas `netem` : utiliser une machine virtuelle Linux standard (cas à tester notamment sous WSL2).

---

## 3. Contenu

| Fichier | Rôle |
|---|---|
| `../01_base.sh` | Construit le banc de base (deux espaces de noms, trois liens, profils `netem`, application `10.99.0.1`). À lancer avec `sudo`. |
| `sla_controller.py` | Mini-contrôleur SD-WAN : mesure les 3 liens, choisit, bascule la route. Écrit `sla_log.csv`. |
| `ping_app.log` | *(généré)* Trafic témoin vers l'application, avec horodatage. |
| `sla_log.csv` | *(généré)* Mesures du contrôleur : `t_s, lien, rtt_ms, perte_pct, sla_ok, choisi`. |
| `README.md` | Ce document. |

Les chemins ci-dessous supposent l'organisation du dépôt `partie1/lab1_1_sdwan/` ; les commandes se lancent **depuis le dossier du lab**. Adapter `../01_base.sh` si votre arborescence diffère.

---

## 4. Monter le banc et le contrôler

```bash
sudo bash ../01_base.sh
sudo ip netns exec agence ping -c 5 10.1.0.2     # attendu : RTT proche de 20 ms
sudo ip netns exec agence ping -c 5 10.2.0.2     # attendu : proche de 40 ms
sudo ip netns exec agence ping -c 5 10.3.0.2     # attendu : proche de 60 ms
sudo ip netns exec agence tc qdisc show          # les 3 profils netem sont visibles
```

Les RTT mesurés doivent être proches du tableau (à 10 % près). **Ne pas poursuivre si le banc n'est pas sain.**

---

## 5. Expérience

Deux terminaux sont nécessaires. Le contrôleur doit tourner **avant** le ping témoin : tant qu'il n'a pas posé de route, l'agence n'a aucune route vers `10.99.0.1`.

**1. Monter le banc de base** (§ 4).

**2. Terminal A — lancer le contrôleur**

```bash
date +%s.%N                      # heure de démarrage, pour convertir les temps relatifs du contrôleur
sudo python3 sla_controller.py
```

**3. Terminal B — lancer un trafic témoin vers l'application**

```bash
sudo ip netns exec agence ping -D -i 0.2 10.99.0.1 | tee ping_app.log
```

**4. Dégrader le lien 1 dans les deux sens**, en notant l'heure juste avant :

```bash
date +%s.%N
sudo ip netns exec agence tc qdisc change dev a1 root netem delay 120ms loss 5% rate 20mbit
sudo ip netns exec dc     tc qdisc change dev d1 root netem delay 120ms loss 5% rate 20mbit
```

**5. Observer** la bascule dans le terminal A et le changement de RTT dans le ping témoin.

**6. Rétablir le lien 1** (délai 10 ms, perte 0 %) et observer le retour au lien préféré :

```bash
sudo ip netns exec agence tc qdisc change dev a1 root netem delay 10ms loss 0% rate 20mbit
sudo ip netns exec dc     tc qdisc change dev d1 root netem delay 10ms loss 0% rate 20mbit
```

Arrêter le contrôleur avec `Ctrl+C`, puis archiver les mesures brutes (voir § 8).

### Fonctionnement du contrôleur

À chaque cycle (`PERIODE_S = 2` s), `sla_controller.py` :

1. mesure chaque lien par `ping -c 10 -i 0.2 -W 1` depuis l'espace de noms `agence` (RTT moyen et pourcentage de perte) ;
2. retient les liens qui respectent le SLA (`RTT < 100 ms` et `perte < 1 %`) ;
3. choisit le premier de la liste d'ordre de préférence 1 → 2 → 3 ; si **aucun** lien ne respecte le SLA, il prend celui dont le RTT est le plus faible ;
4. si le choix change, remplace la route : `ip -n agence route replace 10.99.0.1/32 via 10.<i>.0.2 dev a<i>`, et affiche `[ t s] bascule vers le lien <i>` ;
5. écrit une ligne par lien et par cycle dans `sla_log.csv`.

---

## 6. Résultats

> Section à remplir après exécution. Ne rien inventer : seules les mesures du groupe comptent, et tout écart avec le guide se note dans le journal de laboratoire.

### 6.1 Environnement

| Élément | Valeur |
|---|---|
| Machine / VM | |
| Noyau (`uname -r`) | |
| iproute2 (`ip -V`) | |
| `tc` (`tc -V`) | |
| Python (`python3 --version`) | |

### 6.2 Mesures à relever

| Moment | Lien choisi | RTT du ping témoin | Perte du ping témoin | Durée de bascule |
|---|---|---|---|---|
| Avant dégradation | | | | — |
| Après dégradation du lien 1 | | | | |
| Après rétablissement | | | | |

La **durée de bascule** est l'écart entre l'heure de la dégradation (`date +%s.%N` noté à l'étape 4) et la bascule affichée par le contrôleur. Le contrôleur affiche un temps relatif à son démarrage : ajoutez-le à l'heure notée à l'étape 2. L'horodatage de `ping -D` (`ping_app.log`) est, lui, en secondes absolues.

### 6.3 Protocole de répétition

Règles d'hygiène du guide (§ 2.5) à appliquer :

- un seul paramètre change à la fois (ici : l'état du lien 1) ;
- au moins **10 répétitions** par condition ; reporter la **médiane** et une dispersion (écart-type ou quartiles) ;
- faire un tour à vide avant de mesurer et ignorer la première mesure ;
- noter les versions des logiciels et la commande exacte ;
- contrôler que le banc est sain avant chaque série (`ping` des liens, `tc qdisc show`) ;
- ne jamais conclure sur une seule exécution.

| Durée de bascule (s) | Dégradation → lien choisi | Rétablissement → retour au lien 1 |
|---|---|---|
| Médiane | | |
| Dispersion | | |
| Nombre de répétitions | | |

Les CSV bruts ne se modifient jamais à la main ; les tableaux et graphiques sont produits par un script d'analyse versionné avec les données.

### 6.4 Valeurs attendues (à confronter aux mesures)

- Avant dégradation, si le lien 1 est choisi : RTT du ping témoin ≈ 20 ms.
- Si le trafic restait sur le lien 1 dégradé : RTT ≈ 240 ms (deux fois 120 ms), au-dessus du seuil de 100 ms.
- Après bascule vers le lien 2 : RTT ≈ 40 ms ; vers le lien 3 : ≈ 60 ms.

---

## 7. Analyse

À rédiger par le groupe. Points à traiter :

1. **Pourquoi préférer le lien 1** quand il respecte le SLA, plutôt que de toujours prendre le meilleur RTT ?
2. **Que se passe-t-il quand les trois liens violent le SLA**, et ce comportement est-il satisfaisant ?
3. **Comment relier la définition de MEF 70.x** (un service) **et l'architecture contrôleur-edge** de la diapositive 4 ?
4. **Temps de bascule :** une boucle de mesure de 3 liens à 10 sondes espacées de 0,2 s dure plusieurs secondes (environ 2 s de sondes par lien, mesurées l'une après l'autre, plus la pause de 2 s : estimation d'après le script) ; le temps de bascule est du même ordre. Le syllabus cite un BFD à 300 ms (diapositive 29) : comparer et expliquer pourquoi un vrai SD-WAN détecte plus vite.
5. **Granularité de la perte :** avec 10 sondes par mesure, la perte mesurée avance par pas de 10 %. Le seuil `perte < 1 %` revient donc à n'accepter **aucune** sonde perdue. Quelles conséquences sur le choix entre les liens 2 et 3, dont le profil comporte déjà des pertes ?

| Question | Réponse |
|---|---|
| 1 | |
| 2 | |
| 3 | |
| 4 | |
| 5 | |

---

## 8. Archiver les résultats

Le dépôt sépare les données brutes, les figures et les scripts :

```bash
cp sla_log.csv ../resultats/lab1_1_sla_log.csv     # CSV brut, jamais modifié à la main
cp ping_app.log ../resultats/lab1_1_ping_app.log
```

Commiter les résultats bruts **avec** le script d'analyse, et pas seulement les graphiques. Noter dans `journal/` (un fichier daté par séance) : date, objectif, commandes lancées, versions, résultats, écarts constatés par rapport au guide.

---

## 9. Nettoyage

À la fin de la séance :

```bash
sudo ip netns del agence ; sudo ip netns del dc
```

Cela supprime les deux espaces de noms, les `veth` et les profils `netem`.

---

## 10. Ce que ce lab ne reproduit pas

Le lab illustre **seulement la politique SLA**. Il n'a :

- ni plan de contrôle séparé ;
- ni tunnels IPsec ;
- ni protocole d'overlay ;
- ni classification applicative (DPI).

SASE et SSE (diapositives 4 et 30) sont des catégories d'analystes, pas des normes. Extension optionnelle, à détailler en Partie 7 : placer un espace de noms « PoP » avec un proxy filtrant devant le lien Internet.

Comme tout banc d'émulation, celui-ci répond à une question précise : il ne prouve pas que le réseau réel se comporte de la même façon. L'émulateur de liens a aussi ses limites, par exemple la granularité de l'horloge du noyau, qui peut perturber débit et délai.

---

## 11. Dépannage

| Symptôme | Cause probable | Que faire |
|---|---|---|
| `sudo modprobe sch_netem` échoue | Le noyau n'a pas `netem` (cas à tester sous WSL2) | Utiliser une machine virtuelle Linux standard |
| `ip netns add` répond « File exists » | Un banc précédent n'a pas été nettoyé | Lancer la commande de nettoyage (§ 9), puis relancer `01_base.sh` |
| `ping` vers `10.99.0.1` : « Network is unreachable » | Le contrôleur n'est pas lancé, donc aucune route | Lancer `sla_controller.py` avant le ping témoin |
| RTT très différents du tableau | Banc non sain, ou profil `netem` mal appliqué | Relire `tc qdisc show` côté `agence` **et** côté `dc` |

---

## 12. Statut de vérification

Selon le guide de simulation (version du 5 novembre 2026) : la syntaxe des scripts a été contrôlée (`bash -n`, `py_compile`) et l'analyse de la sortie de `ping` a été testée sur des exemples, mais **aucune commande réseau n'a été exécutée** dans l'environnement de rédaction (les outils `ip` et `tc` y sont absents). Le statut de ce lab est donc **« À tester »** : le groupe doit l'exécuter et consigner les écarts dans le journal.

## Références

- Guide de simulation — INF4087 Réseaux II (WAN avancé), version du 5 novembre 2026 : § 2.4 (poste de travail), § 2.5 (hygiène expérimentale), § 2.6 (organisation du dépôt), § 3.2 (banc de base), § 3.3 (lab 1.1).
- Syllabus INF4087 : diapositives 4 (architecture contrôleur-edge, SASE/SSE), 29 (valeurs SLA voix, BFD à 300 ms) et 30.