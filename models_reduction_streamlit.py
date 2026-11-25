# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 14:24:57 2024

@author: fages1
"""
import sys
# sys.path.append('C:/Users/fages1/OneDrive - Universite de Lorraine/Code_these/PAH/')
import time
import datetime
import pickle 
import os 
from TIRAMISU import read_model_new as rm
from TIRAMISU import make_translation as mt
from TIRAMISU import add_and_write_mechanism as awm
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import re
#%%
cloud="Nextcloud"
pick=True
trad=False
path_mech_core=f'C:/Users/fages1/Nextcloud/Code_these/Reduction/ALV2BN+T+LV23_V3/NoNox/+metathesis/+change_C5H4CH3/+slow_toluene/ALV2BN+T+L23_V3_reduced_O2C3_V3_V2_NN.mech'
path_therm_core=f'C:/Users/fages1/Nextcloud/Code_these/Reduction/ALV2BN+T+LV23_V3/NoNox/+metathesis/+change_C5H4CH3/+slow_toluene/ALV2BN+T+L23_V3_reduced_O2C3_V3_V2_NN.therm'
path_trans_core=f'C:/Users/fages1/Nextcloud/Code_these/Reduction/ALV2BN+T+LV23_V3/NoNox/+metathesis/+change_C5H4CH3/+slow_toluene/ALV2BN+T+L23_V3_reduced_O2C3_V3_V2_NN.trans'
output_name=f'C:/Users/fages1/Nextcloud/Code_these/Reduction/ALV2BN+T+LV23_V3/dump/'
output_gen=output_name
n=150000

if pick == True :
    time_start = time.time()
    model_core=rm.Model(path_mech_core, path_therm_core, output_name, path_trans_core)
    time_end=time.time()
    print(f'{time_end-time_start:.2f} s')
    print(f'Number of species / reactions : {len(model_core.reactions[1])} / {len(model_core.reactions[2])}')
    with open(f'{output_name}model_core.pick', 'wb') as m2 :
        pickle.dump(model_core, m2)


else :

    with open(f'{output_name}model_core.pick', 'rb') as m2 :
        model_core = pickle.load(m2)
        print(f'Number of species / reactions : {len(model_core.reactions[1])} / {len(model_core.reactions[2])}')

        
#%%
def parse_formula(formula):
    # Use regular expressions to extract counts of C, H, and O atoms
    matches = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
    counts = {'C': 0, 'H': 0, 'O': 0}
    for element, count in matches:
        counts[element] = int(count) if count else 1
    return counts

def sort_key(formula):
    counts = parse_formula(formula)
    return (counts['C'], counts['H'], counts['O'])
#%%


new_model='ALV2BN+T+L23_V3_reduced_O2C3_V1'

O2=[x for x in model_core.spe if 'o' in model_core.therm[x].atomic_composition and model_core.therm[x].atomic_composition['o']>1]
O2C=[x for x in O2 if 'c' in model_core.therm[x].atomic_composition and model_core.therm[x].atomic_composition['c']>2 ]
# print_list2 = [x for x in O2C if 'o' in model_core.therm[x].atomic_composition and model_core.therm[x].atomic_composition['o']>2 ]

print_list = sorted(O2C, key=lambda x: sort_key(model_core.therm[x].raw_formula()))
print(len(print_list))
# print_list= [[x, model_core.therm[x].raw_formula()] for x in print_list]


#%%


awm.writing_modified_mechanism(output_gen, new_model, model_core, list_species=print_list)


#%% 
# REMOVE 1 REA SPECIES
start=3
new_model_start='ALV2BN+T+L23_V3_reduced_O2C3_V'
new_model=f'{new_model_start}{start}'

while True :
    print(f'Enter loop : {start}')
    time_start = time.time()
    path_new_mech=f'{output_gen}{new_model}.mech'
    path_new_therm=f'{output_gen}{new_model}.therm'
    path_new_trans=f'{output_gen}{new_model}.trans'
    model_new=rm.Model(path_new_mech, path_new_therm, output_name, path_new_trans)
    time_end=time.time()
    print(f'{time_end-time_start:.2f} s')
    print(f'Number of species / reactions : {len(model_new.reactions[1])} / {len(model_new.reactions[2])}')
    
    species_occurence={}
    for species in model_new.spe :
        species_occurence[species]=0
    print_list=[]
    for rea in model_new.rea :
        spe_set=set([*rea.species[0], *rea.species[1]])
        for spe in spe_set :
            species_occurence[spe]+=1
    
    print_list=[x for x in species_occurence if species_occurence[x]<=1]
    print_list.remove('he')
    print('len spe_list = ',len(print_list))
    if len(print_list) == 0 :
        break
    
    start+=1
    new_model=f'{new_model_start}{start}'
    awm.writing_modified_mechanism(output_gen, new_model, model_new, list_species=print_list, verbose=False)

species_occurence={}
for species in model_new.spe :
    species_occurence[species]=0
print_list=[]
for rea in model_new.rea :
    spe_set=set([*rea.species[0], *rea.species[1]])
    for spe in spe_set :
        species_occurence[spe]+=1
        
print('Enter final stage one')
print_list=[x for x in species_occurence if species_occurence[x]<=2]
print_list.remove('he')
print_list2=[[x, *model_new.micro_mech([x])[1]] for x in print_list]
print_list3=[x[0] for x in print_list2 if x[1].is_rev==x[2].is_rev and x[1].is_rev==False]
new_model_start=f'ALV2BN+T+L23_V3_reduced_O2C3_V{start}_V'
start=1
new_model=f'{new_model_start}{start}'
print('len spe_list = ',len(print_list3))
awm.writing_modified_mechanism(output_gen, new_model, model_new, list_species=print_list3, verbose=False)
print('Enter final stage two')
time_start = time.time()
path_new_mech=f'{output_gen}{new_model}.mech'
path_new_therm=f'{output_gen}{new_model}.therm'
path_new_trans=f'{output_gen}{new_model}.trans'
model_new=rm.Model(path_new_mech, path_new_therm, output_name, path_new_trans)
time_end=time.time()
print(f'{time_end-time_start:.2f} s')
print(f'Number of species / reactions : {len(model_new.reactions[1])} / {len(model_new.reactions[2])}')

species_occurence={}
for species in model_new.spe :
    species_occurence[species]=0
print_list=[]
for rea in model_new.rea :
    spe_set=set([*rea.species[0], *rea.species[1]])
    for spe in spe_set :
        species_occurence[spe]+=1
print_list=[x for x in species_occurence if species_occurence[x]<=2]
print_list.remove('he')
print_list2=[[x, *model_new.micro_mech([x])[1]] for x in print_list]
print_list4=[x[0] for x in print_list2 if 'duplicate' in x[1].reaction_types]

start=2
new_model=f'{new_model_start}{start}'
print('len spe_list = ',len(print_list4))
awm.writing_modified_mechanism(output_gen, new_model, model_new, list_species=print_list4, verbose=False)

time_start = time.time()
path_new_mech=f'{output_gen}{new_model}.mech'
path_new_therm=f'{output_gen}{new_model}.therm'
path_new_trans=f'{output_gen}{new_model}.trans'
model_new=rm.Model(path_new_mech, path_new_therm, output_name, path_new_trans)
time_end=time.time()
#%%
# print(f'Enter loop : {start}')
# time_start = time.time()
# path_new_mech=f'{output_gen}{new_model}.mech'
# path_new_therm=f'{output_gen}{new_model}.therm'
# path_new_trans=f'{output_gen}{new_model}.trans'
# model_new=rm.Model(path_new_mech, path_new_therm, output_name, path_new_trans)
# time_end=time.time()
# print(f'{time_end-time_start:.2f} s')
# print(f'Number of species / reactions : {len(model_new.reactions[1])} / {len(model_new.reactions[2])}')

species_occurence={}
for species in model_new.spe :
    species_occurence[species]=0
print_list=[]
for rea in model_new.rea :
    spe_set=set([*rea.species[0], *rea.species[1]])
    for spe in spe_set :
        species_occurence[spe]+=1

print_list=[x for x in species_occurence if species_occurence[x]<=2]
print_list.remove('he')
print_list2=[[x, *model_new.micro_mech([x])[1]] for x in print_list]
print_list3=[x for x in print_list2 if x[1].is_rev==x[2].is_rev and x[1].is_rev==False]
print_list4=[x for x in print_list2 if 'duplicate' in x[1].reaction_types]
print(len(print_list3), len(print_list4))
# print_list4=[x for x in print_list3 if (x[0] in x[1].species[0] and x[0] in x[2].species[0])]
# print_list4=print_list4+[x for x in print_list3 if (x[0] in x[1].species[1] and x[0] in x[2].species[1])]
# print(len(print_list4))
# print_list=[x[0] for x in print_list4]
# mol_list=[[x, mech2.therm[x].raw_formula()] for x in print_list if ('h' in mech2.therm[x].atomic_composition and mech2.therm[x].atomic_composition['h']%2==0)]
# test_list=[x for x in mech2.reactions[1] if mech2.therm[x].raw_formula()=='C8H10']
# print_list = sorted(print_list, key=lambda x: sort_key(mech2.therm[x].raw_formula()))
# print(print_list)
# print_list2=[[x, mech2.therm[x].raw_formula(), *mech2.micro_mech([x])[1]] for x in print_list]
# print(print_list)