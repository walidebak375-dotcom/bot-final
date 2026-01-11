dataset = [
    # ========== VLAN SIMPLE ==========
    {
        "question": "comment créer un vlan sur un switch cisco",
        "brand": "Cisco",
        "response": """1. enable
2. configure terminal
3. vlan 10
4. name VLAN_10
5. exit
6. interface fastEthernet 0/1
7. switchport mode access
8. switchport access vlan 10
9. exit
10. end
11. write memory"""
    },
    {
        "question": "créer vlan cisco",
        "brand": "Cisco",
        "response": """1. enable
2. configure terminal
3. vlan 10
4. name VLAN_10
5. exit"""
    },
    
    # ========== VLAN MULTIPLE (NOUVEAU) ==========
    {
        "question": "créer plusieurs vlans cisco",
        "brand": "Cisco",
        "type": "dynamic",
        "template": "multiple_vlans"
    },
    {
        "question": "créer 10 vlan différent cisco",
        "brand": "Cisco",
        "type": "dynamic",
        "template": "multiple_vlans"
    },
    {
        "question": "comment créer 10 vlan différent avec pour chacun 3 ports",
        "brand": "Cisco",
        "type": "dynamic",
        "template": "multiple_vlans_with_ports"
    },
    {
        "question": "créer plusieurs vlan avec ports cisco",
        "brand": "Cisco",
        "type": "dynamic",
        "template": "multiple_vlans_with_ports"
    },
    
    # ========== VLAN JUNIPER ==========
    {
        "question": "comment créer un vlan sur juniper",
        "brand": "Juniper",
        "response": """1. configure
2. set vlans VLAN_10 vlan-id 10
3. set interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members VLAN_10
4. commit"""
    },
    {
        "question": "créer vlan juniper",
        "brand": "Juniper",
        "response": """1. configure
2. set vlans VLAN_10 vlan-id 10
3. commit"""
    },
    {
        "question": "créer plusieurs vlans juniper",
        "brand": "Juniper",
        "type": "dynamic",
        "template": "multiple_vlans_juniper"
    },
    
    # ========== VLAN HP ==========
    {
        "question": "comment créer un vlan sur hp aruba",
        "brand": "HPE",
        "response": """1. configure
2. vlan 10
3. name VLAN_10
4. untagged 1
5. exit
6. write memory"""
    },
    {
        "question": "créer vlan hp",
        "brand": "HPE",
        "response": """1. vlan 10
2. name VLAN_10
3. exit"""
    },
    
    # ========== AUTRES COMMANDES ==========
    {
        "question": "supprimer vlan cisco",
        "brand": "Cisco",
        "response": """1. enable
2. configure terminal
3. no vlan 10
4. end
5. write memory"""
    },
    {
        "question": "supprimer vlan juniper",
        "brand": "Juniper",
        "response": """1. configure
2. delete vlans VLAN_10
3. commit"""
    },
    {
        "question": "comment configurer un trunk cisco",
        "brand": "Cisco",
        "response": """1. enable
2. configure terminal
3. interface fastEthernet 0/2
4. switchport mode trunk
5. switchport trunk allowed vlan 10,20,30
6. exit
7. end
8. write memory"""
    },
    {
        "question": "trunk cisco",
        "brand": "Cisco",
        "response": """1. interface gi0/1
2. switchport mode trunk
3. switchport trunk allowed vlan all
4. exit"""
    },
    {
        "question": "trunk juniper",
        "brand": "Juniper",
        "response": """1. configure
2. set interfaces ge-0/0/2 unit 0 family ethernet-switching interface-mode trunk
3. set interfaces ge-0/0/2 unit 0 family ethernet-switching vlan members [10 20 30]
4. commit"""
    },
    {
        "question": "trunk hp aruba",
        "brand": "HPE",
        "response": """1. configure
2. vlan 10 tagged 1
3. vlan 20 tagged 1
4. exit"""
    },
    {
        "question": "activer spanning tree cisco",
        "brand": "Cisco",
        "response": """1. enable
2. configure terminal
3. spanning-tree mode rapid-pvst
4. exit"""
    },
    {
        "question": "portfast cisco",
        "brand": "Cisco",
        "response": """1. interface range fa0/1 - 24
2. spanning-tree portfast
3. exit"""
    },
    {
        "question": "root bridge cisco",
        "brand": "Cisco",
        "response": """1. spanning-tree vlan 10 root primary
2. exit"""
    },
    {
        "question": "spanning tree juniper",
        "brand": "Juniper",
        "response": """1. configure
2. set protocols rstp interface all
3. commit"""
    },
    {
        "question": "stp hp",
        "brand": "HPE",
        "response": """1. spanning-tree
2. spanning-tree mode rapid-pvst
3. exit"""
    },
    {
        "question": "voir les vlans cisco",
        "brand": "Cisco",
        "response": """show vlan brief"""
    },
    {
        "question": "afficher vlan cisco",
        "brand": "Cisco",
        "response": """show vlan"""
    },
    {
        "question": "voir les vlans juniper",
        "brand": "Juniper",
        "response": """show vlans"""
    },
    {
        "question": "voir les vlans hp",
        "brand": "HPE",
        "response": """show vlan"""
    },
    {
        "question": "voir la config cisco",
        "brand": "Cisco",
        "response": """show running-config"""
    },
    {
        "question": "voir config juniper",
        "brand": "Juniper",
        "response": """show configuration"""
    },
    {
        "question": "voir les interfaces cisco",
        "brand": "Cisco",
        "response": """show ip interface brief"""
    },
    {
        "question": "statut interfaces cisco",
        "brand": "Cisco",
        "response": """show interfaces status"""
    },
    {
        "question": "voir interfaces juniper",
        "brand": "Juniper",
        "response": """show interfaces terse"""
    },
    {
        "question": "mac address table cisco",
        "brand": "Cisco",
        "response": """show mac address-table"""
    },
    {
        "question": "table mac juniper",
        "brand": "Juniper",
        "response": """show ethernet-switching table"""
    },
    {
        "question": "configurer ip interface cisco",
        "brand": "Cisco",
        "response": """1. interface vlan 10
2. ip address 192.168.10.1 255.255.255.0
3. no shutdown
4. exit"""
    },
    {
        "question": "ip juniper",
        "brand": "Juniper",
        "response": """1. configure
2. set interfaces vlan unit 10 family inet address 192.168.10.1/24
3. commit"""
    },
    {
        "question": "passerelle par défaut cisco",
        "brand": "Cisco",
        "response": """1. ip default-gateway 192.168.1.1
2. exit"""
    },
    {
        "question": "route statique cisco",
        "brand": "Cisco",
        "response": """1. ip route 0.0.0.0 0.0.0.0 192.168.1.254
2. exit"""
    },
    {
        "question": "port security cisco",
        "brand": "Cisco",
        "response": """1. interface fa0/1
2. switchport mode access
3. switchport port-security
4. switchport port-security maximum 2
5. switchport port-security violation restrict
6. exit"""
    },
    {
        "question": "désactiver port cisco",
        "brand": "Cisco",
        "response": """1. interface fa0/5
2. shutdown
3. exit"""
    },
    {
        "question": "activer port cisco",
        "brand": "Cisco",
        "response": """1. interface fa0/5
2. no shutdown
3. exit"""
    },
    {
        "question": "mot de passe console cisco",
        "brand": "Cisco",
        "response": """1. line console 0
2. password cisco123
3. login
4. exit"""
    },
    {
        "question": "mot de passe enable cisco",
        "brand": "Cisco",
        "response": """1. enable secret cisco123
2. exit"""
    },
    {
        "question": "ssh cisco",
        "brand": "Cisco",
        "response": """1. hostname Switch1
2. ip domain-name lab.local
3. crypto key generate rsa modulus 2048
4. line vty 0 4
5. transport input ssh
6. login local
7. exit
8. username admin privilege 15 secret cisco123"""
    },
    {
        "question": "sauvegarder config cisco",
        "brand": "Cisco",
        "response": """write memory
ou
copy running-config startup-config"""
    },
    {
        "question": "sauvegarder juniper",
        "brand": "Juniper",
        "response": """commit
ou
commit and-quit"""
    },
    {
        "question": "effacer config cisco",
        "brand": "Cisco",
        "response": """write erase
reload"""
    },
    {
        "question": "ping cisco",
        "brand": "Cisco",
        "response": """ping 192.168.1.1"""
    },
    {
        "question": "traceroute cisco",
        "brand": "Cisco",
        "response": """traceroute 8.8.8.8"""
    },
    {
        "question": "tester connectivité juniper",
        "brand": "Juniper",
        "response": """ping 192.168.1.1 count 5"""
    },
]
