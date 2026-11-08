#!/usr/bin/env bash

# Banc de base de la Partie 1 : agence et datacenter relies par 3 liens
(lancer avec sudo)
set -euo pipefail

ip netns add agence
ip netns add dc

# Profil de chaque lien, applique dans CHAQUE sens (le RTT vaut donc 2 x le delai)
declare -A DELAI=( [1]='10ms' [2]='20ms 5ms' [3]='30ms 15ms' )
declare -A PERTE=( [1]='0%' [2]='0.5%' [3]='1%' )
declare -A DEBIT=( [1]='20mbit' [2]='50mbit' [3]='30mbit' )

for i in 1 2 3; do
    ip link add a$i type veth peer name d$i
    ip link set a$i netns agence
    ip link set d$i netns dc
    ip -n agence addr add 10.$i.0.1/24 dev a$i
    ip -n dc addr add 10.$i.0.2/24 dev d$i
    ip -n agence link set a$i up
    ip -n dc link set d$i up
    # netem agit en sortie : on l'applique des deux cotes du lien
    ip netns exec agence tc qdisc add dev a$i root netem delay ${DELAI[$i]}
loss ${PERTE[$i]} rate ${DEBIT[$i]}
    ip netns exec dc tc qdisc add dev d$i root netem delay ${DELAI[$i]}
loss ${PERTE[$i]} rate ${DEBIT[$i]}
done

ip -n agence link set lo up
ip -n dc link set lo up
ip -n dc addr add 10.99.0.1/32 dev lo # l'application hebergee au
datacenter
echo 'Banc pret. Test : sudo ip netns exec agence ping -c 3 10.1.0.2'