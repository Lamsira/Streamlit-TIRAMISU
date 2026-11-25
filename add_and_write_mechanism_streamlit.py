import copy
import re
import os

def recursive_addition(to_add_mech, model1_translated, model2, warning, depth=1e10) :
    warn_to_check=set()
    new_species=[]
    skip=0
    for species in to_add_mech :
        if species not in model1_translated.reactions[1] :
            print(f'ERROR : {species} not in model1')
            print(species, to_add_mech)
            print(model1_translated.reactions[1])
            return('')
        if species in model2.spe :
            
            while True and skip !=1 :
                conti=input(f'I think the mech {species} is already in model2. Do you want to continue (y/y_all/n)?')
                if conti == 'y' or conti == 'Y':
                    break
                if conti == 'y_all' :
                    skip = 1
                    break
                elif conti == 'n' or conti == 'N' :
                    return('ERROR : already in model2')
        new_species.append([species, model1_translated.spe_model[species]])
    new_reactions=[]
    
    n_species=[x for x,y in new_species]
    count_depth=0
    last_reactions=[]
    while (n_species != [] and count_depth < depth) :
        print(n_species)
        last2_reactions = copy.deepcopy(last_reactions)
        last_reactions=[]
        count_depth+=1
        tmp_n_species=copy.deepcopy(n_species)
        n_species = []
        if tmp_n_species != [] :
            for n_spe in tmp_n_species :
                count=0
                for reaction in model1_translated.reactions[2] :

                    if n_spe in reaction.species[0] or n_spe in reaction.species[1] :

                        if reaction in model2.reactions[2] :
                            print(reaction.species, "Error ?")

                        else :

                            if reaction not in new_reactions :
                                new_reactions.append(reaction)
                            else :
                                
                                len1=len([0 for x in new_reactions[new_reactions.index(reaction)].supinfo if x.strip().startswith('dup')])
                                len2=len([0 for x in reaction.supinfo if x.strip().startswith('dup')])   
                                if len1 == 0 and len2 != 0 :
                                    print(f'\nERROR LUMPING : {new_reactions[new_reactions.index(reaction)].__dict__} {reaction.__dict__}\n')
                                    new_reactions.remove(reaction)
                                    new_reactions.append(reaction)
                                    last_reactions.append(reaction)
                                elif len1 != 0 and len2 != 0 :
                                    xor=[rea.speed for rea in new_reactions if rea==reaction]
                                    # print(f'Faux xor : {xor}')
                                    if reaction.speed not in xor :
                                        new_reactions.append(reaction)
                                        last_reactions.append(reaction)
                                    # print(f'Xor : {xor}')
                            # print(f'{" + ".join(reaction.species[0])} = {" + ".join(reaction.species[1]):30}   {reaction.third_body.upper() if reaction.third_body!=0 else ""}')
                            for side in reaction.species :
                                for species in side :

                                    if species == "hv" :
                                        print(f'REGARDE ! UN PHOTON ! {reaction.species}')
                                    if species != "hv" and species not in [x for x,y in new_species] \
                                    and species not in model2.spe :
                                        if species in warning :
                                            print(f'WARNING : {species} ENCOUNTERED IN REACTION AND NOT TRADUCTED (!CHECK)')
                                            warn_to_check.add(species)

                                        n_species.append(species)
                                        new_species.append([species, model1_translated.spe_model[species]])

                        count+=1
        else :
            break
            # list_to_check=[]
            # for reaction in last_reactions :
            #     for species in [*reaction.species[0],reaction.species[1]]
            
            
            # print(count)
    for ind_spe, species in enumerate([x for x,y in new_species].copy()) :
        if species in model2.reactions[1] :
            print('Already there ....', species)
            del new_species[ind_spe]
    for reaction in new_reactions :
        len1=len([0 for x in reaction.supinfo if x.strip().startswith('dup')])
        if len1 != 0 :
            len2=len([0 for x in new_reactions if x==reaction])
            if len2 == 1 :
                print(f'\nA reaction have been duplicated :\n{reaction.__dict__}\n')
                new_reactions.append(reaction)
            elif len2 < 1 :
                print('FATAL ERROR')
            
        
    print(f'DEPTH = {count_depth}')
    print(f'\nNumber of species that can cause issue : {len(warn_to_check)}\n {warn_to_check}')
    return(new_reactions, new_species)

def mechanism_writing(outp, md1, md2, model1_translated, model2, to_add, custom='') :
    
    """ MECH """
    
    with open(outp+'.mech', 'w') as out :

        """ INTRODUCTION """

        out.write(custom)

        """ ELEMENTS """

        out.write('elements\n'.upper())
        elements=set(model1_translated.reactions[0]+model2.reactions[0])
        for element in elements :
            out.write(f'{element}\n'.upper())

        """ SPECIES 2 """

        out.write(f'end\n{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" SPECIES":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\nspecies\n'.upper())
        for species in model2.reactions[1] :
            out.write(f'{species}\n'.upper())

        """ SPECIES 1 """

        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" SPECIES":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        if to_add != '' :
            for species in to_add[1] :
                out.write(f'{species}\n'.upper())

        """ REACTIONS 2 """

        out.write(f'end\n{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" REACTIONS":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\nreactions\n'.upper())
        for reaction in model2.reactions[2] :
            if reaction.is_rev == True :
                equal= '='
            elif reaction.is_rev == False :
                equal= '=>'
            else :
                print(f'ERROR, NO REV {reaction.__dict__}')

            if reaction.third_body != 0 :
                tb=f"+{reaction.third_body}"
                if reaction.supinfo != [] :
                    low_check=["low/" for x in reaction.supinfo if 'low/' in x or 'low /' in x]
                    tcheb_check=["tcheb/" for x in reaction.supinfo if 'tcheb/' in x or 'tcheb /' in x]
                    if len(low_check) >= 1 or len(tcheb_check) >= 1 :
                        tb=f"(+{reaction.third_body})"
            else :
                tb=''

            reactant=[]
            product=[]
            # print(reaction.speed[1])
            for s, c in zip(reaction.species[0], reaction.coef[0]) :
                if c == 1 :
                    c=''
                elif int(c) == c :
                    c=int(c)
                reactant.append(str(c) + str (s))

            for s, c in zip(reaction.species[1], reaction.coef[1]) :
                if c == 1 :
                    c=''
                elif int(c) == c :
                    c=int(c)
                product.append(str(c) + str (s))

            final_reaction=f'{"+".join(reactant)}{tb if tb!= "" else ""}{equal}{"+".join(product)}{tb if tb!= "" else ""}'
            # to_write=f'{final_reaction:48} {reaction.speed[0]}{reaction.speed[1]:<+7.3f}{reaction.speed[2]:+11.3e}'
            to_write='{:<48}{:>+12.3e}{:>+9.3f}{:>+11.1f}'.format\
            (final_reaction, reaction.speed[0], reaction.speed[1], reaction.speed[2])
            if len(to_write)>80 :
                print(f'Reaction from base model too big ! :\n{to_write}')
                to_write=re.sub(r"\s+", " ", to_write)
                print(to_write)
            out.write((to_write+'\n').upper())
            # print(to_write,len(to_write))
            for sup in reaction.supinfo :
                out.write(('\t'+sup+'\n').upper())
    
            """ REACTIONS 1 """

        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" REACTIONS":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        if to_add != '' :
            
            for reaction in to_add[0] :

                if reaction.is_rev == True :
                    equal= '='
                elif reaction.is_rev == False :
                    equal= '=>'
                else :
                    print(f'ERROR, NO REV {reaction.__dict__}')

                if reaction.third_body != 0 :
                    tb=f"+{reaction.third_body}"
                    if reaction.supinfo != [] :
                        low_check=["low/" for x in reaction.supinfo if 'low/' in x or 'low /' in x]
                        tcheb_check=["tcheb/" for x in reaction.supinfo if 'tcheb/' in x or 'tcheb /' in x]
                        if len(low_check) >= 1 or len(tcheb_check) >= 1 :
                            tb=f"(+{reaction.third_body})"
                else :
                    tb=''

                reactant=[]
                product=[]
                # print(reaction.speed[1])
                for s, c in zip(reaction.species[0], reaction.coef[0]) :
                    if c == 1 :
                        c=''
                    elif int(c) == c :
                        c=int(c)
                    reactant.append(str(c) + str (s))

                for s, c in zip(reaction.species[1], reaction.coef[1]) :
                    if c == 1 :
                        c=''
                    elif int(c) == c :
                        c=int(c)
                    product.append(str(c) + str (s))

                final_reaction=f'{"+".join(reactant)}{tb if tb!= "" else ""}{equal}{"+".join(product)}{tb if tb!= "" else ""}'
                to_write='{:<48}{:>+12.3e}{:>+9.3f}{:>+11.1f}'.format\
                (final_reaction, reaction.speed[0], reaction.speed[1], reaction.speed[2])
                # to_write=f'{final_reaction:48} {reaction.speed[0]:<+12.3e}{reaction.speed[1]:<+7.3f}{reaction.speed[2]:+11.3e}'
                if len(to_write)>80 :
                    print(f'Reaction from added model too big !\n{to_write}')
                    to_write=re.sub(r"\s+", " ", to_write)
                    print(to_write)
                                     
                out.write((to_write+'\n').upper())
                # print(to_write,len(to_write))
                for sup in reaction.supinfo :
                    out.write(('\t'+sup+'\n').upper())
        out.write('end'.upper())
    
    """ THERMO """
    
    with open(outp+'.therm', 'w') as out :
        
        """ INTRODUCTION """

        out.write(custom)
        
        """ START """
        
        out.write(f'thermo\n{300:>10.3f}{1000:>10.3f}{5000:>10.3f}\n'.upper())
        
        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" THERMO":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        
        for species in model2.reactions[1] :
            name=model2.therm[species]
            ato_comp=name.atomic_composition
            string=''
            for  ato in ato_comp :
                string+=ato+' '*(5-len(str(ato_comp[ato]))-len(ato))+str(ato_comp[ato])
#           
            temp=name.temp_list
            
            out.write(f'{name.species:<16}{" "*8}{string:<20}G{temp[0]:>10.2f}{temp[2]:>10.2f}{temp[1]:>8.2f}{" "*6}1\n'.upper())
            for idx,item in enumerate(name.nasa_list) :
                if idx in [4,9,13] :
                    
                    if idx == 4 :
                        strsup='    2'
                    if idx == 9 :
                        strsup='    3'
                    if idx == 13 :
                        strsup=' '*15+'    4'
                        
                    out.write(f'{item:>+15.8e}{strsup}\n'.upper())
                else :
                    out.write(f'{item:>+15.8e}'.upper())
        
        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" THERMO":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        if to_add != '' :
            for species in to_add[1] :
                name=model1_translated.therm[species]
                ato_comp=name.atomic_composition
                string=''
                for  ato in ato_comp :
                    string+=ato+' '*(5-len(str(ato_comp[ato]))-len(ato))+str(ato_comp[ato])
    #           
                temp=name.temp_list

                out.write(f'{name.species:<16}{" "*8}{string:<20}G{temp[0]:>10.2f}{temp[2]:>10.2f}{temp[1]:>8.2f}{" "*6}1\n'.upper())
                for idx,item in enumerate(name.nasa_list) :
                    if idx in [4,9,13] :

                        if idx == 4 :
                            strsup='    2'
                        if idx == 9 :
                            strsup='    3'
                        if idx == 13 :
                            strsup=' '*15+'    4'

                        out.write(f'{item:>+15.8e}{strsup}\n'.upper())
                    else :
                        out.write(f'{item:>+15.8e}'.upper())
                    
        out.write('end'.upper())
        
    """ TRANSPORT """
    
    with open(outp+'.trans', 'w') as out :
        
        """ INTRODUCTION """
        
        out.write(custom)
        
        """ START """
        
        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" TRANSPORT":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        
        for species in  model2.reactions[1] :
            
            trans=model2.trans[species]
            out.write(f'{trans.species:<20}{trans.geo:>10.0f}{trans.lj_p:>10.3f}{trans.lj_cd:>10.3f}{trans.dp:>10.3f}{trans.p:>10.3f}{trans.rr:>10.3f} ! {trans.comment}\n'.upper())
            
        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" THERMO":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        if to_add !='' and model1_translated.path_trans != '':
            for species in  to_add[1] :

                trans=model1_translated.trans[species]
                out.write(f'{trans.species:<20}{trans.geo:>10.0f}{trans.lj_p:>10.3f}{trans.lj_cd:>10.3f}{trans.dp:>10.3f}{trans.p:>10.3f}{trans.rr:>10.3f}\n'.upper())
        else :
            if model1_translated.path_trans == '' :
                out.write('NOT COMPLETE\nNOT COMPLETE\n')
        out.write('end'.upper())

def merging(outp, md_core, md_to_translate, max_len_name, model_core, model_to_translate_translated, order, custom='',flag_extraction=False, to_add=[], encoding='utf-8', keep_all=False, add_origin=True) :
    #(out+f'_{order}', md_translate, md_core, max_len_name, model_to_translate_translated, model_core, order, custom=introduction, flag_extraction=flag_extraction, to_add=to_add)


    def write_species(out, model1, model2, md1, md2, max_len_name, flag_extraction=False, to_add=[], add_origin=True) :
        # out.write(f'end\nspecies\n'.upper())#'{"!"*80}\n!!{" "*76}!!\n!!{"SPECIES":^76}!!\n!!{" "*76}!!\n{"!"*80}\nspecies\n'.upper())
        out.write(f'end\n{"!"*80}\n!!{" "*76}!!\n!!{"SPECIES":^76}!!\n!!{" "*76}!!\n{"!"*80}\nspecies\n'.upper())
        spe_list=[]
        for species in model1.spe :
            if species not in spe_list :
                spe_list.append(species)
                a_o=f'*:_:*{model1.spe_model[species][0]:^{max_len_name+2 if max_len_name != "" else 20}}*:_:*' if add_origin==True else ''
                out.write((f'{species:<80}'+f'\t! {a_o} {model1.spe_model[species][1].strip()}\n').upper())

        if flag_extraction == True :
            # out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" SPECIES":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            for species in to_add[1] :
                if species[0] not in spe_list :
                    spe_list.append(species)
                    if species[0] not in model1.spe :
                        a_o=f'*:_:* {species[1]} *:_:*' if add_origin==True else ''
                        out.write((f'{species[0]:<80}'+f'\t! {a_o} \n').upper())
        elif model2 != '' :
            # out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" SPECIES":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            for species in model2.spe :
                if species not in spe_list :
                    spe_list.append(species)
                    a_o=f'*:_:* {model2.spe_model[species][0]} *:_:*' if add_origin==True else ''
                    out.write((f'{species:<80}'+f'\t! {a_o}{model2.spe_model[species][1]}\n').upper())


    def write_reactions(out, model1, model2, md1, md2, max_len_name, flag_extraction=False, to_add=[], add_origin=True) :
        out.write(f'end\n{"!"*80}\n!!{" "*76}!!\n!!{"REACTIONS":^76}!!\n!!{" "*76}!!\n{"!"*80}\nreactions\n'.upper())

        # out.write(f'end\nreactions\n'.upper())#{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" REACTIONS":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\nreactions\n'.upper())
        rea_list=[]
        for reaction in model1.rea :
            if reaction not in rea_list :
                rea_list.append(reaction)
                out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
            else :
                identical_rea=[x for x in rea_list if x==reaction]
                new=True
                for r in identical_rea :
                    if r.model != reaction.model :
                        new=False
                        break
                    elif r.is_rev == False and reaction.is_rev == False :
                        if [set(r.species[0]),set(r.species[1])] == [set(reaction.species[1]),set(reaction.species[0])] :
                            print('Complementary irreversible reaction found.')
                            break
                        elif 'duplicate' not in r.reaction_types or 'duplicate' not in reaction.reaction_types :
                            new=False
                            break
                        elif r.identifier == reaction.identifier :
                            new=False
                            break
                    elif 'duplicate' not in r.reaction_types or 'duplicate' not in reaction.reaction_types :
                        new=False
                        break
                    elif r.identifier == reaction.identifier :
                        new=False
                        break
                if new == True :
                    rea_list.append(reaction)
                    out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                else :
                    if model2=='' :
                        rea_list.append(reaction)
                        out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                        reaction.print_reaction()
                    else :
                        print('Part1 Rea skipped because it should already be in the mechanism :')
                        reaction.print_reaction()
        if flag_extraction == True :
            # out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" REACTIONS":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())

            for reaction in to_add[0] :
                if reaction not in rea_list :
                    rea_list.append(reaction)
                    out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                else :
                    identical_rea=[x for x in rea_list if x==reaction]
                    new=True
                    for r in identical_rea :
                        if r.model != reaction.model :
                            new=False
                            break
                        elif r.is_rev == False and reaction.is_rev == False :
                            if [set(r.species[0]),set(r.species[1])] == [set(reaction.species[1]),set(reaction.species[0])] :
                                print('Complementary irreversible reaction found.')
                                break
                            elif 'duplicate' not in r.reaction_types or 'duplicate' not in reaction.reaction_types :
                                new=False
                                break
                            elif r.identifier == reaction.identifier :
                                new=False
                                break
                        elif 'duplicate' not in r.reaction_types or 'duplicate' not in reaction.reaction_types :
                            new=False
                            break
                        elif r.identifier == reaction.identifier :
                            new=False
                            break
                    if new == True :
                        rea_list.append(reaction)
                        out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                    else :
                        print('Part2 Rea skipped because it should already be in the mechanism :')
                        reaction.print_reaction()
        elif model2 !='' :
            # out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" REACTIONS":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            rea_list_model2=[]
            for reaction in model2.rea :
                if reaction not in rea_list :
                    rea_list_model2.append(reaction)
                    rea_list.append(reaction)
                    out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                else :
                    identical_rea=[x for x in rea_list if x==reaction]
                    new=True
                    for r in identical_rea :
                        if r.model != reaction.model :
                            new=False
                            break
                        elif r.is_rev == False and reaction.is_rev == False :
                            if [set(r.species[0]),set(r.species[1])] == [set(reaction.species[1]),set(reaction.species[0])] :
                                print('Complementary irreversible reaction found.')
                                break
                            elif 'duplicate' not in r.reaction_types or 'duplicate' not in reaction.reaction_types :
                                new=False
                                break
                            elif r.identifier == reaction.identifier :
                                new=False
                                break
                        elif 'duplicate' not in r.reaction_types or 'duplicate' not in reaction.reaction_types :
                            new=False
                            break
                        elif r.identifier == reaction.identifier :
                            new=False
                            break
                    if new == True :
                        rea_list.append(reaction)
                        out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                    else :
                        
                        if reaction in rea_list_model2 :
                            print(f'Rea duplicate undeclared in model2. Maybe third body ? Rea added anyway.')
                            reaction.print_reaction()
                            for rea in rea_list :
                                if reaction==rea :
                                    rea.print_reaction()
                            rea_list.append(reaction)
                            out.write(reaction.print_reaction(path='return', pr=False, max_len_name=max_len_name, add_origin=add_origin))
                        else :    
                            print('Part3 Rea skipped because it should already be in the mechanism :')
                            reaction.print_reaction()
                            for rea in rea_list :
                                if reaction==rea :
                                    rea.print_reaction()
                        
        out.write('end'.upper())


    def write_therm(out, model1, model2, md1, md2, flag_extraction=False, to_add=[], keep_all=False, add_origin=True) :
        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" THERMO":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        spe_list=[]
        # print(f'model1 : {model1.path_mech}')
        # for species in model1.spe :
        in_which_spe_list=model1.spe if keep_all is False else model1.therm
        print((1, len(model1.spe)) if keep_all is False else (0, len(model1.therm)))
        for species in in_which_spe_list :
            if species not in spe_list :
                # print(species)
                spe_list.append(species)
                name=model1.therm[species]
                ato_comp=name.atomic_composition
                string=''
                # if len(ato_comp)> 5 :
                count = 0
                long_atom_list=False
                string_lal=''
                if len(ato_comp) > 4 :
                    string+='H   0'
                    for ato in ato_comp :
                        long_atom_list = True
                        count += 1
                        string_lal+=ato+' '+str(ato_comp[ato])+' '
                else :
                    for ato in ato_comp :
                        string+=ato+' '*(5-len(str(ato_comp[ato]))-len(ato))+str(ato_comp[ato])
                        count += 1
                # for  ato in ato_comp :
                #     if count >= 4:
                #         long_atom_list = True
                #         count += 1
                #         string_lal+=ato+' '+str(ato_comp[ato])+' '
                #     else :    
                        
                    
            
                temp=name.temp_list
                a_o=f'*:_:* {name.from_model if name.from_model != '' else''} *:_:*' if add_origin==True else ''
                # new_write=f'{to_write}\t! {a_o} {reaction_com}\n'
                if long_atom_list==False :
                    new_write=f'{name.species:<16}{" "*8}{string:<20}G{temp[0]:>10.2f}{temp[2]:>10.2f}{temp[1]:>8.2f}{" "*6}1'
                    new_write+=f'! {a_o} {"! "+name.comment if name.comment.strip() !="" else ""}\n'
                    out.write(new_write.upper())
                else :
                    new_write=f'{name.species:<16}{" "*8}{string:<20}G{temp[0]:>10.2f}{temp[2]:>10.2f}{temp[1]:>8.2f}{" "*6}1&'
                    new_write+=f'! {a_o} {"! "+name.comment if name.comment.strip() !="" else ""}\n'
                    out.write(new_write.upper())
                    out.write(f'{string_lal}\n'.upper())
            
                for idx,item in enumerate(name.nasa_list) :
                    if idx in [4,9,13] :
                        
                        if idx == 4 :
                            strsup='    2'
                        if idx == 9 :
                            strsup='    3'
                        if idx == 13 :
                            strsup=' '*15+'    4'
                            
                        out.write(f'{item:>+15.8e}{strsup}\n'.upper())
                    else :
                        out.write(f'{item:>+15.8e}'.upper())        
        
        if flag_extraction == True :
            out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" THERMO":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            for species in to_add[1] :
                if species[0] not in spe_list :
                    spe_list.append(species[0])
                    name=model2.therm[species[0]]
                    ato_comp=name.atomic_composition
                    string=''
                    for  ato in ato_comp :
                        string+=ato+' '*(5-len(str(ato_comp[ato]))-len(ato))+str(ato_comp[ato])
                
                    temp=name.temp_list
                    
                    out.write(f'{name.species:<16}{" "*8}{string:<20}G{temp[0]:>10.2f}{temp[2]:>10.2f}{temp[1]:>8.2f}{" "*6}1\n'.upper())
                
                    for idx,item in enumerate(name.nasa_list) :
                        if idx in [4,9,13] :
                            
                            if idx == 4 :
                                strsup='    2'
                            if idx == 9 :
                                strsup='    3'
                            if idx == 13 :
                                strsup=' '*15+'    4'
                                
                            out.write(f'{item:>+15.8e}{strsup}\n'.upper())
                        else :
                            out.write(f'{item:>+15.8e}'.upper())       
        elif model2 !='' :
            out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" THERMO":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            for species in model2.spe :
                if species not in spe_list :
                    spe_list.append(species)
                    name=model2.therm[species]
                    ato_comp=name.atomic_composition
                    string=''
                    for  ato in ato_comp :
                        string+=ato+' '*(5-len(str(ato_comp[ato]))-len(ato))+str(ato_comp[ato])
                
                    temp=name.temp_list
                    
                    out.write(f'{name.species:<16}{" "*8}{string:<20}G{temp[0]:>10.2f}{temp[2]:>10.2f}{temp[1]:>8.2f}{" "*6}1\n'.upper())
                
                    for idx,item in enumerate(name.nasa_list) :
                        if idx in [4,9,13] :
                            
                            if idx == 4 :
                                strsup='    2'
                            if idx == 9 :
                                strsup='    3'
                            if idx == 13 :
                                strsup=' '*15+'    4'
                                
                            out.write(f'{item:>+15.8e}{strsup}\n'.upper())
                        else :
                            out.write(f'{item:>+15.8e}'.upper()) 
        
        out.write('end'.upper())



    def write_trans(out, model1, model2, md1, md2, flag_extraction=False, to_add=[],keep_all=False) :
        spe_list=[]
        out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md1+" TRANSPORT":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
        in_which_spe_list=model1.spe if keep_all is False else model1.trans
        for species in in_which_spe_list :
            if species not in spe_list :
                spe_list.append(species)
                trans=model1.trans[species]
                out.write(f'{trans.species:<20}{trans.geo:>10.0f}{trans.lj_p:>10.3f}{trans.lj_cd:>10.3f}{trans.dp:>10.3f}{trans.p:>10.3f}{trans.rr:>10.3f} !{trans.comment}\n'.upper())
        if flag_extraction == True :
            out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" TRANSPORT":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            for species in to_add[1] :
                if species[0] not in spe_list :
                    spe_list.append(species[0])
                    trans=model2.trans[species[0]]
                    out.write(f'{trans.species:<20}{trans.geo:>10.0f}{trans.lj_p:>10.3f}{trans.lj_cd:>10.3f}{trans.dp:>10.3f}{trans.p:>10.3f}{trans.rr:>10.3f} !{trans.comment}\n'.upper())
        elif model2 !='' :
            out.write(f'{"!"*80}\n!!!!!{" "*70}!!!!!\n!!!!!{md2+" TRANSPORT":^70}!!!!!\n!!!!!{" "*70}!!!!!\n{"!"*80}\n'.upper())
            for species in model2.spe :
                if species not in spe_list :
                    spe_list.append(species)
                    trans=model2.trans[species]
                    out.write(f'{trans.species:<20}{trans.geo:>10.0f}{trans.lj_p:>10.3f}{trans.lj_cd:>10.3f}{trans.dp:>10.3f}{trans.p:>10.3f}{trans.rr:>10.3f} !{trans.comment}\n'.upper())
        out.write('end'.upper())

    """ MECH """
    
    with open(outp+'.mech', 'w', encoding=encoding) as out :

        """ INTRODUCTION """
        out.write(f'! encoding = {encoding}\n')
        out.write(custom)
        out.write('! TIRAMISU order = '+order+'\n')
        
        """ ELEMENTS """

        out.write('elements\n'.upper())
        elements=set(model_core.elem+model_to_translate_translated.elem if model_to_translate_translated != '' else model_core.elem)
        
        for element in elements :
            out.write(f'{element}\n'.upper())
        
        """ SPECIES """
        if 'k' in order  :
            
            write_species(out, model_core, model_to_translate_translated, md_core, md_to_translate,max_len_name, flag_extraction, to_add, add_origin=add_origin)
            write_reactions(out, model_core, model_to_translate_translated, md_core, md_to_translate, max_len_name, flag_extraction, to_add, add_origin=add_origin)
            
        else :
            
            write_species(out, model_to_translate_translated, model_core, md_to_translate, md_core,max_len_name, flag_extraction, to_add, add_origin=add_origin)
            write_reactions(out, model_to_translate_translated, model_core, md_to_translate, md_core, max_len_name, flag_extraction, to_add, add_origin=add_origin)

    """ THERMO """

    with open(outp+'.therm', 'w', encoding=encoding) as out :

        """ INTRODUCTION """
        out.write(f'!encoding = {encoding}\n')
        out.write(custom)
        out.write('!TIRAMISU order = '+order+'\n')

        """ START """
        
        out.write(f'thermo\n{300:>10.3f}{1000:>10.3f}{5000:>10.3f}\n'.upper())
        
        if 't' in order :
            
            write_therm(out, model_core, model_to_translate_translated, md_core, md_to_translate, flag_extraction, to_add, keep_all = keep_all,  add_origin=add_origin)
            
        else :
            write_therm(out, model_to_translate_translated, model_core, md_to_translate, md_core, flag_extraction, to_add, keep_all = keep_all,  add_origin=add_origin)
        
    """ TRANSPORT """
    if (model_core.path_trans != '' and model_to_translate_translated == '') or (model_core.path_trans != '' and model_to_translate_translated.path_trans != '') :
        with open(outp+'.trans', 'w', encoding=encoding) as out :
            
            """ INTRODUCTION """
            out.write(f'!encoding = {encoding}\n')
            out.write(custom)
            out.write('!TIRAMISU order = '+order+'\n')
    
            """ START """
            
            if 't' in order :
                write_trans(out, model_core, model_to_translate_translated, md_core, md_to_translate, flag_extraction, to_add, keep_all = keep_all)
            else :
                write_trans(out, model_to_translate_translated, model_core, md_to_translate, md_core, flag_extraction, to_add, keep_all = keep_all)
            
def writing_modified_mechanism(outp, new_md_name, true_model, list_species=[], list_reactions=[], dict_translation={}, verbose=True, custom='', keep_all=False, add_origin=True) :
    
    model=copy.deepcopy(true_model)
    # for species in list_species :
    
    # print(f'nb reaction {len(write[1])}')
    print(len(model.spe), len(list_species))
    
    if list_species != [] :
        rea_removed=[]
        spe_removed=[]
        for spe in copy.deepcopy(model.reactions[1]) :
            if spe in list_species :
                # print([spe])
                spe_removed.append(model.reactions[1].pop(model.reactions[1].index(spe)))
                model.therm.pop(spe)
                model.trans.pop(spe)
           
        # print(len(model.spe))

        for rea in copy.deepcopy(model.reactions[2]) :
            testing=[x for x in [*rea.species[0],*rea.species[1]] if x in list_species]
            if len(testing)>0 :
                # print(testing)
                for index,r in enumerate(model.reactions[2]) :
                    if r.eq_rea(rea) :
                        # print('a ',index)
                        break
                # print('b ',index)
                rea_removed.append(copy.deepcopy(model.reactions[2][index]))
                del model.reactions[2][index]
    
        with open(outp+new_md_name+'_spe&rea_removed.txt', 'w') as s_r :
            for spe in spe_removed :
                s_r.write(f'{spe}\n')
            
        for rea in rea_removed :
            if verbose == True :
                rea.print_reaction(outp+new_md_name+'_spe&rea_removed.txt')
                
        print('nb rea removed because of spe :', len(rea_removed))
        print('nb spe removed :',len(spe_removed))
    
    if list_reactions != [] :
        rea_force_removed=[]
        for rea in list_reactions :
            for index,r in enumerate(copy.deepcopy(model.reactions[2])) :         
                if r.eq_rea(rea) :
                    rea_force_removed.append(copy.deepcopy(model.reactions[2][index]))
                    del  model.reactions[2][index]
                    break
            
        with open(outp+new_md_name+'_spe&rea_force_removed.txt', 'w') as cl :
            pass
        for rea in rea_force_removed :
            rea.print_reaction(outp+new_md_name+'_spe&rea_force_removed.txt', pr=False)
        print('nb rea force removed :', len(rea_force_removed))
    
    if dict_translation != {} :
        for spe in copy.deepcopy(model.reactions[1]) :
            # print(spe)
            if spe in dict_translation :
                print('1 :'+spe)
                tmp_spemodel=model.spe_model.pop(spe)
                tmp=model.reactions[1].index(spe)
                model.reactions[1][tmp] = dict_translation[spe]
                model.spe_model[dict_translation[spe]]=tmp_spemodel
                print('2 :'+model.reactions[1][tmp])
                model.therm[dict_translation[spe]]=model.therm.pop(spe)
                model.therm[dict_translation[spe]].species=dict_translation[spe]
                model.trans[dict_translation[spe]]=model.trans.pop(spe)
                model.trans[dict_translation[spe]].species=dict_translation[spe]

        # for spe in dict_translate :
        for index,rea in enumerate(copy.deepcopy(model.reactions[2])) :    
            for index2, side in enumerate(rea.species) :
                for index3, spe in enumerate(side) :                                                     
                    if spe in dict_translation :
                        print(f'before : {model.reactions[2][index].species}')
                        model.reactions[2][index].species[index2][index3] = dict_translation[spe]
                        print(f'after : {model.reactions[2][index].species}')

    
    spe_removed=[]
    spe_set=set()        
                                                            
    for rea in copy.deepcopy(model.reactions[2]) :
        for spe in [*rea.species[0], *rea.species[1]] :
            spe_set.add(spe)

    for spe in copy.deepcopy(model.reactions[1]) :
        if spe not in spe_set and spe not in ['he', 'ar', 'ne']+[x for x in model.coll_species]:
            print('No reaction for',spe)
            spe_removed.append(model.reactions[1].pop(model.reactions[1].index(spe)))
            model.therm.pop(spe)
            if hasattr(model,'trans') :
                model.trans.pop(spe)
    
    with open(outp+new_md_name+'_norea_spe_removed.txt', 'w') as nr_s :
        for spe in spe_removed :
            nr_s.write(f'{spe}\n')
    # print(len(model.spe))
    merging(outp+new_md_name, 'model', '', max(list(set([len(x.from_model) if x.from_model != '' else len(x.model) for x in model.rea]))),
            model, '', 'kt', custom=custom ,flag_extraction=False, to_add=[], keep_all=keep_all, add_origin=add_origin)

    
    return(model)
    
        