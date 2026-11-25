import numpy as np
import os
import re
import copy
from collections import Counter

class Model :
    def __init__(self, path_mech, path_therm, path_trans='', encoding='utf-8', base_mechanism='', keep_all=False):

        self.path_mech = path_mech
        self.path_therm = path_therm
        self.encoding=encoding
        self.base_mechanism=base_mechanism
        self.keep_all=keep_all
        self.coll_species=set()
        self.spe_model={}
        self.reactions= self.read_model()
        self.therm = self.read_therm()
        if path_trans != '' :
            self.path_trans = path_trans
            # print(path_trans)
            self.trans = self.read_trans()
            self.check, self.new_t = (self.atomic_conservation(), self.check_therm_trans())

        else :
            self.path_trans = ''
            self.check = self.atomic_conservation()

        self.rea=self.rea
        self.isomer_groups=self.get_isomers()
        
            
    def select_reactions(self, which=[]) :
        if which == [] :
            return([x for x in self.reactions[2]])
        else :
            to_return=[]
            for typ in which :
                to_return+=[x for x in self.reactions[2] if typ in x.reaction_types]
                # to_return+=[x.reaction_types for x in self.reactions[2]]
                # print(to_return)
            return(to_return)
    
    def read_model(self) :

        reactions=[]

        # print('\n',f'\n {self.path_mech}')
        
        """---------------------------------------------------------------------
                                   READING MECHANISM   
        ---------------------------------------------------------------------"""
        # try :
        with open (self.path_mech,'r', encoding=self.encoding,errors='backslashreplace') as open_mech :
            read_mech=open_mech.readlines()
        index_line=0
        
        """---------------------------------------------------------------------
                                   PURGING MECHANISM  
        ---------------------------------------------------------------------"""

        #### Replacing float number like .x by 0.x (.3 into 0.3)
        # [print(''.join([re.sub(r'\+\.','+0.',re.sub(r'=\.','=0.',re.sub(r'>\.','>0.' ,re.sub(r'\s\.', ' 0.',line.split('!')[0])))), *line.split('!')[1:]])) for line in read_mech]
        # (re.sub(r'\+\.','+0.',re.sub(r'=\.','=0.',re.sub(r'>\.','>0.' ,re.sub(r'\s\.', ' 0.', line.split('!')[0]))))for line in read_mech)
        purged_mech=['!'.join([re.sub(r'\+\.','+0.',re.sub(r'=\.','=0.', re.sub(r'>\.','>0.' ,re.sub(r'\s\.', ' 0.', line.split('!')[0])))),
                               *line.split('!')[1:]]) for line in read_mech]
        
        #### Removing every comments (!***) and blank lines
        purged_mech=[line.strip() for line in purged_mech if line.strip() != ''
                     and line.strip()[0] != '!']
        
        #### Removing every useless white space (in reactions and multiples 
        #### white spaces)
        # purged_mech=[re.sub("\s+", " ", line.split('!')[0]) 
        #              for line in purged_mech]     
        purged_mech=[re.sub(r"\s+", " ", line) 
                      for line in purged_mech] 
        
        purged_mech=[re.sub('> ','>',re.sub(
            ' <', '<',re.sub(r'[= ][= ]+','=',re.sub(r'\+ ', '+', line)))) 
                     for line in purged_mech]
        
        #### Split Comment
        purged_mech=[line.split('!') for line in purged_mech]
        
        for entireline in purged_mech.copy() :
            line=entireline[0]
            listplus=(re.findall(r' \+', line))
            tmpline=line
            for iterplus in listplus :
                tmpnumb=tmpline[tmpline.index(' +')+2:].split(' ')[0]
                try : 
                    float(tmpnumb) 
                    break
                except ValueError :
                    tmpline=tmpline.replace(' +', '+', 1)
            purged_mech[purged_mech.index(entireline)][0]=tmpline
            
        for entireline in purged_mech.copy() :
            
            line=entireline[0]
            listplus=(re.findall(r' \(\+', line))
            tmpline=line
            for iterplus in listplus :
                tmpnumb=tmpline[tmpline.index(' (+')+3:].split(' ')[0]
                try : 
                    float(tmpnumb)
                    break
                except ValueError :
                    tmpline=tmpline.replace(' (+', '(+', 1)
            purged_mech[purged_mech.index(entireline)][0]=tmpline
        
        
        for ind,line in enumerate(purged_mech.copy()) :
            purged_mech[ind][0]=purged_mech[ind][0].lower()
            
        for x in purged_mech :
            if '!' in x[0] : 
                print(f'warning {x[0]}')
      
        """------------------------------------------------------------------"""

        len_mech = len(purged_mech)
        elements = []
        species = []

        index_line=0

        """---------------------------------------------------------------------
                                   READING ELEMENTS  
        ---------------------------------------------------------------------"""
        print(f'\n------------------------------{os.path.basename(self.path_mech)}------------------------------\n')
        while 'elem' not in purged_mech[index_line][0].strip().split()[0] :
            index_line+=1
        # print(f'LINE FOR START OF ELEMENTS : {purged_mech[index_line][0]}')
        index_start=True
        # index_line+=1
        while 'end' not in purged_mech[index_line][0].strip().split()[0] :
            if index_start :
                tmplist=[y for x,y in enumerate(purged_mech[index_line][0].split()) if x != 0]
                index_start=False
            else :
                tmplist=purged_mech[index_line][0].split()
            for ele in tmplist :
                elements.append(ele)
            index_line+=1
        # print(f'LINE FOR END OF ELEMENTS : {purged_mech[index_line][0]}')
        index_line+=1
        if elements==[] :
            raise Exception('List of elements is empty.')
        

        #### check if blank
        [print('BLANK ELEMENT !!!!!!!') for ele in elements if ele=='']
        
        """---------------------------------------------------------------------
                                   READING SPECIES  
        ---------------------------------------------------------------------"""

        while 'spe' not in purged_mech[index_line][0].strip().split()[0]:
            index_line+=1
        # print(f'LINE FOR START OF SPECIES : {purged_mech[index_line][0]}')
        index_line+=1
        while 'end' not in purged_mech[index_line][0].strip().split()[0] :
            tmplist=purged_mech[index_line][0].split()
            for spe in tmplist :
                if spe in species :
                    #print('Mech duplicate :',spe, index_line, purged_mech[index_line])
                    pass
                else :
                    comment='!'.join(purged_mech[index_line][1:])
                    if '*:_:*' in comment :
                        
                        from_model = comment.split('*:_:*')[1].strip()
                        self.spe_model[spe]=[from_model, comment.split('*:_:*')[2]]
                    else :
                        if self.base_mechanism != '' :
                            from_model=self.base_mechanism
                        else :
                            from_model=os.path.splitext(os.path.basename(self.path_mech))[0]
                        self.spe_model[spe]=[from_model, comment]
                    species.append(spe)
            index_line+=1
        # print(f'LINE FOR END OF SPECIES : {purged_mech[index_line][0]}')
        index_line+=1


        #### check if blank
        if self.path_mech!=self.path_therm : 
            [print('BLANK SPECIES !!!!!!!') for spe in species if spe=='']
        else :
            print('Mech == Therm')
        """---------------------------------------------------------------------
                                   READING REACTIONS  
        ---------------------------------------------------------------------"""
        
        while 'rea' not in purged_mech[index_line][0].strip().split()[0]  and 'maxsp' not in purged_mech[index_line][0]:
            index_line+=1
        
        if 'maxsp' in purged_mech[index_line][0] :
            print('WARNING : MAXSP HERE')
        # print(f'LINE FOR START OF REACTIONS : {purged_mech[index_line][0]}')
        
        count_of_not_int = 0
        index_line+=1

        from_model=''

        initiation=0
        
        identifier=0
        sup_i=[]
        reactant,product=[],[]
        stoechio_coef=[]
        rev=''
        speed=[]
        third_body=''
        while 'end' not in purged_mech[index_line][0].strip().split()[0] :
            line=purged_mech[index_line][0]

            #### if '=' in line, it's a reaction line
            if '=' in line :
               
                if initiation!=0 :
                    reaction_types=[]
                    
                    for info in sup_i :
                        
                        if 'plog' in info and 'plog' not in reaction_types :
                            reaction_types.append('plog')
                        
                        elif 'troe' in info and all(t not in reaction_types for t in ['troe', 'low/troe', 'high/troe']):
                            reaction_types.append('troe')
                        
                        elif 'low' in info and 'troe' in reaction_types :
                            reaction_types.remove('troe')
                            reaction_types.append('low/troe')
                            
                        elif 'low' in info and 'low/troe' not in reaction_types :
                            if 'low' in info and 'low' not in reaction_types : 
                                reaction_types.append('low')
                            
                        elif 'high' in info and 'troe' in reaction_types :
                            reaction_types.remove('troe')
                            reaction_types.append('high/troe')
                            
                        elif 'high' in info and 'high/troe' not in reaction_types :
                            if 'high' in info and 'high' not in reaction_types : 
                                reaction_types.append('high')
                                
                        elif 'dup' in info and 'duplicate' not in reaction_types :
                            reaction_types.append('duplicate')
                        elif 'rev' in info and 'rev_keyword' not in reaction_types :
                            reaction_types.append('rev_keyword')
                        elif 'cheb' in info and 'cheb' not in reaction_types :
                            reaction_types.append('cheb')
                        elif 'sri' in info and 'high' in reaction_types :
                            if 'troe' in reaction_types or 'high/troe' in reaction_types :
                                raise Exception(sup_i)
                            else :
                                reaction_types.remove('high')
                                reaction_types.append('high/sri')
                        
                        else :
                            nb_occurence=0
                            temp_inf=info.replace('/', ' ')
                            temp_inf=temp_inf.split()
                            for word in temp_inf :
                                if word in ['plog', 'low', 'dup', 'rev', 'cheb'] :
                                    nb_occurence+=1
                                    
                            if nb_occurence>= 2 :
                                print(f'WARNING IN SUPINFO : {info}')
                            if nb_occurence == 0 :
                                for word in temp_inf :
                                    if word in ['colleff','exci','fit1','ford','jan','lt','mome','rlt','rord', 'tdep', 'usrprog', 'units'] :
                                        raise Exception(f'KeyWordError : {info}')
                        
                    if ('low/troe' in reaction_types and 'high' in reaction_types) or ('high/troe' in reaction_types and 'low' in reaction_types):
                        print(f"Low and High Troe at the same time ! {identifier}\n{sup_i}")
                        
                    # if third_body != 0 and third_body != 'm' :
                    #     print(f"Watch reaction {identifier} ! +{third_body} efficiency need to be set to 0 in all other duplicate reactions !")
                    
                    reactions.append(Reactions([reactant,product],
                                stoechio_coef, rev, speed, sup_i, third_body, comment, reaction_types, identifier, from_model, 
                                os.path.splitext(os.path.basename(self.path_mech))[0]))
                    if third_body != 0 and third_body != 'm' :
                        print(f"Watch reaction {identifier} ! +{third_body} efficiency need to be set to 0 in all other duplicate reactions !")
                        reactions[-1].print_reaction()
                    elif third_body == 'm' :
                        # pattern = r'^\s*(?:[A-Za-z0-9\-\+]+ *\/ *[-+Ee.0-9]+ *\/\s*)+$'
                        pattern = r'^\s*(?:[A-Za-z0-9\-\+]+\s*/\s*[-+]?(?:\d*\.\d+|\d+\.\d*|\d+)(?:[eE][-+]?\d+)?\s*/\s*)+$'
                        temp_collision_efficiency=set()
                        for i_line in sup_i :
                            
                            if bool(re.match(pattern, i_line.strip())) :
                                # print('yolo')
                                tmp_i_line=[x.strip() for x in i_line.split('/')[:-1] if i_line.split('/')[:-1].index(x) % 2 == 0]
                                for i in tmp_i_line :
                                    if i not in species :
                                        raise Exception(f'Collision efficiency error, {i} not in species')
                                    else :
                                        self.coll_species.add(i)
                        
                    
                    identifier+=1
                    #appel classe
               
                if len(purged_mech[index_line])>1 :
                    try :
                        comment='!'.join(purged_mech[index_line][1:])
                        if '*:_:*' in comment :
                            from_model = comment.split('*:_:*')[1].strip()
                        else :
                            if self.base_mechanism != '' :
                                from_model=self.base_mechanism
                            else :
                                from_model=''
                    except TypeError :
                        print(f'INT OBJECT IS NOT SUBSCRIPTABLE : {purged_mech[index_line][1:]}')
                        comment='!'.join([str(x) for x in purged_mech[index_line][1:]])
                        print(comment)
                else :
                    comment=''
                    if self.base_mechanism != '' :
                        from_model=self.base_mechanism
                    else :
                        from_model=''
                    
                
                
    
                sup_i=[]

            #### splitting reaction line into [reaction, A, n, Ea]
                third_body=0
                line=line.split()
                if len(line)!=4 :
                    print(f'Old line = {line}')
                    line=[''.join(line[0:-3]),line[-3],line[-2],line[-1]]
                    print(f'New line = {line}')

                reaction=line[0]
                
                if '.' in reaction : count_of_not_int+=1 #print('Not int species : ', reaction)
                speed=[]
                for speed_coef in line[1:] :
            #### if one of speed_coef is badly written (not a number), append a
            #### 0 instead. (created due to some numbers written 0.0000+03 
            #### instead of 0.0000E+03 in LLNL) 
                    try :
                        speed.append(float(speed_coef.replace('d', 'e')))
                        if 'd' in speed_coef :
                            print(f'WARNING IN THE MODEL {speed_coef} (should work)')
                    except ValueError :
                        speed.append(0)
                        print(f'One of them is transformed into 0 : {line[1:]}')
            #### check if the reaction is reversible or not and split into
            #### [reactant, product] (and check if a reaction as been written 
            #### "in reverse" with a <=)
                if '<=>' in reaction : 
                    rev=True
                    reaction=reaction.split('<=>')
                elif '<=' in reaction :
                    rev=False
                    reaction=reaction.split('<=')

                    print('Reaction written in a wrong way ....', reaction)
                    reaction=[reaction[1],reaction[0]]
                    print('Reaction written in a good way ....', reaction)

                elif '=>' in reaction :
                    rev=False
                    reaction=reaction.split('=>')

                else :
                    rev=True
                    reaction=reaction.split('=')

            #### protect third body (like (+M) or (+H2O)) 
                if '(+' in reaction.copy()[0] :
                    third_body = reaction[0][reaction[0].index('(+')+2 : -1]
                    reaction[0] = reaction[0][:reaction[0].index('(+')]
                    reaction[1] = reaction[1][:reaction[1].index('(+')]

            #### split species

                reactant=reaction[0].split('+')

                product=reaction[1].split('+')
            #### removing third body disguised in species ....
                if 'm' in reactant :
                    if 'm' not in product or third_body != 0 :
                        print('Third_body ERROR !! Either third_body'\
                              'protection as failed or a third_body is only in'\
                              'one side of the reaction (reactant) ',
                              third_body, reaction)
                    else :
                        third_body = 'm'
                        reactant.remove('m')
                        product.remove('m')

                if 'm' in product :
                    print('Third_body ERROR !!A third_body is only in one side'\
                          'of the reaction (product)', third_body, reaction)


            #### reading the stoechiometric coefficient before each species 
                stoechio_coef=[[],[]]

            #### for reactant
                for rea in reactant.copy() :
                    stoe_rea=''
                    tmp_rea_index=0
                    while rea[tmp_rea_index].isnumeric() == True \
                    or rea[tmp_rea_index]=='.' :

                        stoe_rea+=rea[tmp_rea_index]
                        tmp_rea_index+=1
                    
                    if stoe_rea=='' :
                        stoe_rea=1
                    else :
#                         print(reactant)
                        reactant[reactant.index(rea)]=rea[tmp_rea_index:]
#                         print(reactant)
                    stoechio_coef[0].append(float(stoe_rea))
            #### for product
                for prod in product.copy() :
                    stoe_prod=''
                    tmp_prod_index=0
                    try :
                        while prod[tmp_prod_index].isnumeric() == True \
                        or prod[tmp_prod_index]=='.' :
                            
                            stoe_prod+=prod[tmp_prod_index]
                            tmp_prod_index+=1
                    except IndexError :
                        raise Exception(f'IndexError in : {prod} {product} {reaction} {tmp_prod_index}')
                        
                    if stoe_prod=='' :
                        stoe_prod=1
                    else :
#                         print(product)
                        product[product.index(prod)]=prod[tmp_prod_index:]
#                         print(product)
                    stoechio_coef[1].append(float(stoe_prod))

            #### removing multiple species occurence and summing their 
            #### stoechiometric coeffiscient for reactant
                stop_loop1=0
                while [1 for spe in Counter(reactant) if \
                       Counter(reactant)[spe]>1] != [] :

                    stop_loop1+=1
                    tmp_counter= [spe for spe in Counter(reactant) \
                                  if Counter(reactant)[spe]>1]
                    
                    species_idx = [i for i, item in enumerate(reactant) \
                                   if tmp_counter[0] == item]
                    
                    stoechio_coef[0][species_idx[0]]=sum(\
                        [x for num,x in enumerate(stoechio_coef[0])\
                         if num in species_idx])
                    
                    stoechio_coef[0]=[x for num,x in \
                    enumerate(stoechio_coef[0]) if num not in species_idx[1:]]
                    reactant=[x for num,x in enumerate(reactant) \
                              if num not in species_idx[1:]]

                    if stop_loop1>=4 :
                        print('FATAL ERROR IN WHILE LOOP FOR stoechio_coef '+
                              'MERGE')
                        break

            #### for product
                stop_loop2=0        
                while [1 for spe in Counter(product) 
                       if Counter(product)[spe]>1] != [] :

                    stop_loop2+=1
                    tmp_counter= [spe for spe in Counter(product) 
                                  if Counter(product)[spe]>1]
                    
                    species_idx = [i for i, item in enumerate(product) 
                                   if str(tmp_counter[0]) == str(item)]
#                     print('\n')
#                     for item in product :
#                         print([tmp_counter[0]], [item], re.fullmatch(tmp_counter[0], item))
                    
#                     print(f'{reactant} = {product},\nSt_coef {stoechio_coef[1]},\nSp_idx {species_idx},\ntmp_count {tmp_counter}')
                    
                    stoechio_coef[1][species_idx[0]]=sum([x for num,x in enumerate(stoechio_coef[1])\
                                                          if num in species_idx])
                    
                    stoechio_coef[1]=[x for num,x in enumerate(stoechio_coef[1]) \
                                      if num not in species_idx[1:]]
                    
                    product=[x for num,x in enumerate(product) if num not in species_idx[1:]]

                    if stop_loop2>=4 :
                        print('FATAL ERROR IN WHILE LOOP FOR stoechio_coef MERGE')
                        break


                initiation=1

            else :
                sup_i.append(line)
            index_line+=1
        
        for info in sup_i :
            if 'plog' in info and 'plog' not in reaction_types :
                reaction_types.append('plog')
            if ('low' in info or 'troe' in info) and 'low/troe' not in reaction_types :
                reaction_types.append('low_troe')
            if 'dup' in info and 'duplicate' not in reaction_types :
                reaction_types.append('duplicate')
            if 'rev' in info and 'rev_keyword' not in reaction_types :
                reaction_types.append('rev_keyword')
            if 'cheb' in info and 'cheb' not in reaction_types :
                reaction_types.append('cheb')
                
        if third_body != 0 and third_body != 'm' :
            print(f"Watch reaction {identifier} ! +{third_body} efficiency need to be set to 0 in all other duplicate reactions !")
        reactions.append(Reactions([reactant,product], stoechio_coef, rev, speed, sup_i, third_body, comment, reaction_types, identifier,
                                   from_model, os.path.splitext(os.path.basename(self.path_mech))[0]))
    
        #### if one species start with "(", the code doesn't work anymore
        for spe in species :
            if spe[0] == '(' :
                print('NEED TO CHANGE THE CODE BECAUSE "(" AT THE START OF A SPECIES : ',spe)
        
        ############## WRITING LOGS #################   
        root, extension = os.path.splitext(self.path_mech)
       
        is_in_rea=set()
        for reaction in reactions :
            for side in reaction.species :
                for spe in side :
                    is_in_rea.add(spe)
        print(f'Before removing unused species : {len(species)} species')
        species_removed_init=set()
        for spe in species.copy() :
            if spe not in is_in_rea and spe not in elements+[x for x in self.coll_species] :
                # print(f'{spe} NOT IN REACTIONS')
                species_removed_init.add(spe)
                species.remove(spe)
        print(f'Species removed : {species_removed_init}\nNew number of species : {len(species)} species')

        ############## RETURNING RESULTS ################# 
        print(f'\nNot-int species in {count_of_not_int} reactions')
        print('\nSpecies for collision efficiency :')
        for cs in self.coll_species :
            print(f'{cs}')
        print('End of mech file\n')
        return([elements, species, reactions])
    
    
    """-------------------------------------------------------------------------
    ----------------------------------------------------------------------------
    
                                       THERMO  
                                   
    ----------------------------------------------------------------------------
    -------------------------------------------------------------------------"""
    
    
    def read_therm(self) :
        
        not_in_mech=[]
        therm_duplicate=[]
        therm_data={}
        
        """---------------------------------------------------------------------
                                   READING THERM FILE  
        ---------------------------------------------------------------------"""
        # try :
        with open(self.path_therm, 'r', encoding=self.encoding,errors='backslashreplace') as therm :
            read_therm=therm.readlines()

        """---------------------------------------------------------------------
                                   PURGING THERM FILE  
        ---------------------------------------------------------------------"""

        purged_therm=[line for line in read_therm if line.strip() != '' and line.strip()[0] != '!']
        purged_therm=[line.split('!') for line in purged_therm]
        index=0
        while 'thermo' not in purged_therm[index][0].lower() :
            index+=1
            
        if index != 0 :
            print(f'Number of lines before THERMO or THERMO ALL : {index}')
            purged_therm=purged_therm[index:]
        # if 'thermo' not in purged_therm.lower() :
        #     print('ERROR IN THERMO')
        temperature_save=purged_therm[1][0]
        purged_therm=purged_therm[2:]
        purged_therm=[[y.lower() if x.index(y)==0 else y for y in x ] for x in purged_therm]
        index_line=0

        """---------------------------------------------------------------------
                                   SAVING BASE TEMP  
        ---------------------------------------------------------------------"""

        base_temp=temperature_save.strip().split()
        base_temp=list(map(float, base_temp))
        base_temp=sorted(base_temp)

        multiple_list=[]
        # print(purged_therm)
        """---------------------------------------------------------------------
                                READING SPECIES AND NASA 
        ---------------------------------------------------------------------"""
        # print(self.reactions[1])
        while 'end' not in purged_therm[index_line][0][:10] :
            line=purged_therm[index_line][0]
            # print(line)
            # base_indexline=index_line
            if len(line.strip()) > 80 :
                additional_data=True
            else :
                additional_data=False
            # line = line[:80]
        #### reading species
            # print([purged_therm[index_line]])
            # print(line)
            species=line.strip()[:line.strip().index(' ')]
            # print(species)
        #### counting atomes of each species

            # if species not in multiple_list and line[79]=='1' and species in self.reactions[1] :
            if species not in multiple_list and line[79]=='1'  and (self.keep_all or species in self.reactions[1]):

                multiple_list.append(species)

                
                hidden_formula=line[24:44]
                hidden_formula=re.sub(r'\.',' ',hidden_formula)
                hidden_formula=[hidden_formula[x:x+5] for x in range(0,len(hidden_formula),5)]
                test_added_atoms_1=[line[73:75].strip(), line[75:78].strip()]
                # print(test_added_atoms_1)

                if test_added_atoms_1[0] != '' and test_added_atoms_1[0].isalpha() :
                    if test_added_atoms_1[1] != '' and test_added_atoms_1[1].isdigit():
                        if int(test_added_atoms_1[1]) != 0 :
                           test_added_atoms_1=([test_added_atoms_1[0], int(test_added_atoms_1[1])])
                        else :
                            test_added_atoms_1=[]
                    else :
                        test_added_atoms_1=[]
                else :
                    test_added_atoms_1=[]
                # print(test_added_atoms_1)
                test_added_atoms_2=[]
                
                if additional_data == True :
                    if line[80] == '&' :
                        change_line=True
                        index_line+=1
                        line_ad=purged_therm[index_line][0]
                        matches = re.findall(r'([A-Za-z])\s*(\d+)', line_ad)
                        test_added_atoms_2 = {}
                        for letter, num in matches:
                            test_added_atoms_2[letter] = int(num)
                        
                        while '&' in line_ad :
                            index_line+=1
                            line_ad=purged_therm[index_line][0]
                            matches = re.findall(r'([A-Za-z])\s*(\d+)', line_ad)
                            for letter, num in matches:
                                test_added_atoms_2[letter] = int(num)
                            
                       
                    else :
                        change_line=False
                        test_added_atoms_2=[line[x:x+5] for x in range(80,80+len(line[80:]),5)]
                        if len(test_added_atoms_2[-1])<3 :
                            print(test_added_atoms_2)
                            test_added_atoms_2=test_added_atoms_2[:-1]
                        test_added_atoms_2=[[x[:2].strip(),x[2:].strip()] for x in test_added_atoms_2]
                        for atomedata in copy.deepcopy(test_added_atoms_2) :
                            if atomedata[0] != '' and atomedata[0].isalpha() :
                                if atomedata[1] != '' and atomedata[1].isdigit():
                                    if int(atomedata[1]) != 0 :
                                       test_added_atoms_2.remove(atomedata)
                                       test_added_atoms_2.append([atomedata[0], int(atomedata[1])])
                                    else :
                                        test_added_atoms_2.remove(atomedata)
                                else :
                                    test_added_atoms_2.remove(atomedata)
                            else :
                                test_added_atoms_2.remove(atomedata)
                                
                        test_added_atoms_2={x : y for (x,y) in test_added_atoms_2}
                for num,atomedata in enumerate(hidden_formula) :
                    hidden_formula[num]=atomedata.strip()

                hidden_formula=set(hidden_formula)
                hidden_formula=list(hidden_formula)

                if '0' in hidden_formula or '00' in hidden_formula :
                    hidden_formula=list(filter(lambda a: a != '0' and a != '00', hidden_formula))

                if '' in hidden_formula :
                    hidden_formula=list(filter(lambda a: a != '', hidden_formula))

                tmp_elements_list={}
                
                # print('HD :',hidden_formula)
                for num,atome in enumerate(hidden_formula) :
                    element=atome.split()[0]
                    # print('atome :',atome)
                    if (len(hidden_formula) == 1 and len(atome) == 1) or atome.split()[1] == '0':
                        continue
                    else :
                        nb=atome.split()[1]
                        tmp_elements_list[element]=int(nb)
                if test_added_atoms_1 != [] :
                    if test_added_atoms_1[0] in tmp_elements_list :
                        tmp_elements_list[test_added_atoms_1[0]]+=test_added_atoms_1[1]
                    else :
                        tmp_elements_list[test_added_atoms_1[0]]=test_added_atoms_1[1]
                if test_added_atoms_2 != [] :
                    # print(test_added_atoms_2)
                    for new_atoms in test_added_atoms_2 :
                        if new_atoms in tmp_elements_list :
                            tmp_elements_list[new_atoms]+=test_added_atoms_2[new_atoms]
                        else :
                            tmp_elements_list[new_atoms]=test_added_atoms_2[new_atoms]
                

            #### actual temp integration
                test_temp=0
                try :
                    actual_temp=[float(line[45:55].strip().split()[-1]), float(line[55:65].strip().split()[-1]),
                             float(line[65:73].strip().split()[-1])]
                except IndexError :
                    print(line)
                    print(line[45:55])
                    print(line[55:65])
                    print(line[65:73])
                    actual_temp=[float(line[45:55].strip().split()[-1]), float(line[55:65].strip().split()[-1])]
                # actual_temp=list(map(float, actual_temp))
                actual_temp=sorted(actual_temp)

                if len(actual_temp) == 2 :
                    test_temp=actual_temp.copy()
                    actual_temp.append(base_temp[1])
                    
                elif len(actual_temp) == 0 :
                    actual_temp=base_temp.copy()
                    
                elif len(actual_temp) == 1 : 
                    print(f'ERROR : TOO FEW THERMO TEMPERATURE {len(actual_temp)} FOR {species}')
                actual_temp=sorted(actual_temp)
                
                if actual_temp[1]-actual_temp[0]<300 or actual_temp[2]-actual_temp[1]<500 :
                    print(f'Thermo temperature diff too low !!! : {species}'\
                          f' {actual_temp[1]-actual_temp[0]}, {actual_temp[2]-actual_temp[1]}'\
                          , actual_temp, test_temp)
                    
                split_nasa=[]

            #### NASA reading
                for data_line in range(1, 4) :

                    if data_line==3 :
                        line_nasa=purged_therm[index_line+data_line][0][:60]
                        line_nasa=re.sub('e 0', 'e+0', line_nasa)
                        split_nasa=split_nasa+[float(line_nasa[x:x+15]) for x in range(0, len(line_nasa), 15)]
                        

                        if len(split_nasa) != 14 : print('SPLIT NASA LENGTH = ', len(split_nasa))
                        b_m=self.base_mechanism
                        if len(purged_therm[index_line])>1 :
                            comment='!'.join([x.strip() for x in purged_therm[index_line][1:]])
                            if '*:_:*' in comment :
                                b_m = comment.split('*:_:*')[1].strip()
                                comment='!'.join(comment.split('*:_:*')[2].strip().split('!')[1:])
                            
                        else :
                            comment=''
                        therm_data[species]=(Thermo(species, tmp_elements_list, actual_temp, split_nasa, comment, b_m))
                        index_line+=4
                        

                    else :
                        line_nasa=purged_therm[index_line+data_line][0][:75]
                        line_nasa=re.sub('e 0', 'e+0', line_nasa)
                        # print(species, line_nasa,'\n',[(line_nasa[x:x+15]) for x in range(0, len(line_nasa), 15)] )
                        split_nasa=split_nasa+[float(line_nasa[x:x+15]) for x in range(0, len(line_nasa), 15)]
            else :
                # print(species)
                if species not in self.reactions[1] :
                    # print(f'THERMO DATA NOT IN MECH : {species}')
                    not_in_mech.append(f'THERMO DATA NOT IN MECH : {species}\n')
                else :
                    # print('THERM DUPLICATE : ', species)
                    therm_duplicate.append(f'THERM DUPLICATE : {species}\n')

                index_line+=1

                for k_iter in range(index_line, len(purged_therm)-1) :
                    # print(purged_therm[index_line][0][0:80][0])
                    if len(purged_therm[index_line][0][0:80]) < 80 :
                        index_line+=1
                    elif purged_therm[index_line][0][0:80][-1] != '1' :

                        index_line+=1
                    else :
                        break
        # print(purged_therm[index_line-1])
        
        root, extension = os.path.splitext(self.path_therm)
                
        return(therm_data)

    
    """-------------------------------------------------------------------------
    ----------------------------------------------------------------------------
    
                                    TRANSPORT  
                                   
    ----------------------------------------------------------------------------
    -------------------------------------------------------------------------"""
                
    def read_trans(self) :
        
        trans_data={}
        
        """---------------------------------------------------------------------
                                   READING TRANSPORT   
        ---------------------------------------------------------------------"""
        # try :
        #print(self.path_trans)
        with open (self.path_trans, 'r', encoding=self.encoding) as open_trans :
            read_trans=open_trans.readlines()

        index_line=0
        
        """---------------------------------------------------------------------
                                   PURGING TRANSPORT  
        ---------------------------------------------------------------------"""

        
        #### Removing every comments (!***) and blank lines
        purged_trans=[line.strip() for line in read_trans if line.strip() != ''
                     and line.strip()[0] != '!']

        #### Removing every useless white space (in reactions and multiples 
        #### white spaces)
        # purged_mech=[re.sub(r"\s+", " ", line) 
        #               for line in purged_mech]
        purged_trans=[re.sub(r"\s+", " ", line).split('!') 
                     for line in purged_trans]     
            
        purged_trans=[[y.lower() if x.index(y)==0 else y for y in x] for x in purged_trans]
        # print(purged_trans)
        if 'end' in purged_trans[-1][0] :
            purged_trans=purged_trans[:-1]
            
        not_in_mech=[]
        
        for data_line in purged_trans :
            # print(data_line)
            data = data_line[0].split()
            if len(data) != 7 :
                pass
                # print(data_line,'\n', data)
                
            else :
                # if True :
                if self.keep_all or data[0] in self.reactions[1] :
                    if len(data_line)>1 :
                        comment='!'.join(data_line[1:])
                    else :
                        comment=''
                    trans_data[data[0]]=(Transport(data[0], float(data[1]), float(data[2]), float(data[3]), float(data[4]), float(data[5]), float(data[6]), comment))
                else :
                    # print(f'TRANS DATA NOT IN MECH : {data[0]}')
                    not_in_mech.append(f'TRANS DATA NOT IN MECH : {data[0]}\n')
                    
        root, extension = os.path.splitext(self.path_trans)
        return(trans_data)
                
    
    def create_transport(self,species) :
        LJCD=1.236*(self.therm[species].molecular_mass())**(1/3)
        LJP=37.15*(self.therm[species].molecular_mass())**0.58
        geom= 0 if sum([y for x,y in self.therm[species].atomic_composition.items()]) == 1 else 1 if sum([y for x,y in self.therm[species].atomic_composition.items()]) == 2 else 2
        new_trans=Transport(species.upper(), geom, LJP, LJCD, 0, 0, 1, 'TIRAMISU Estimated Wang and Frenklach 1994')
        self.trans[species]=(new_trans)
        
        # print(f'No transport for : {species.upper()}. New transport created :\n'+
        #       f'{species.upper():<20}{geom:>10.0f}{LJP:>10.3f}{LJCD:>10.3f}{0:>10.3f}{0:>10.3f}{1:>10.3f} ! TIRAMISU Estimated Wang and Frenklach 1994\n')
        print(f'{species.upper():<20}{geom:>10.0f}{LJP:>10.3f}{LJCD:>10.3f}{0:>10.3f}{0:>10.3f}{1:>10.3f} ! TIRAMISU Estimated Wang and Frenklach 1994')
        return(new_trans)
        
    def check_therm_trans(self) :
        new_trans=[]
        for spe in self.spe :
            if spe not in self.therm :
                raise
        if hasattr(self, 'trans') :
            print_bool=False
            for spe in self.spe :
                if spe not in self.trans :
                    if print_bool==False :
                        print(f'Species with no transport. Creating new transport :')
                        print_bool=True
                    new_trans.append(self.create_transport(spe))
                    
        return(new_trans)
                    
                    
    """-------------------------------------------------------------------------
    ----------------------------------------------------------------------------
                            READING SPECIES AND NASA 
    ----------------------------------------------------------------------------
    -------------------------------------------------------------------------"""
    
    def atomic_conservation(self) :
        iso_reactions={}
        for reaction in self.reactions[2] :
#             print(reaction.__dict__)
            reactant=[reaction.species[0],reaction.coef[0]]
            product=[reaction.species[1],reaction.coef[1]]
            rea_dict={}
            prod_dict={}
            # print(reactant)
            for num,rea in enumerate(reactant[0]) :
                if rea != 'hv' :
                    # return(self.therm)
                    
                    rea_tmp=self.therm[rea].atomic_composition
                    for atome in rea_tmp :
                        if atome not in rea_dict :
                            rea_dict[atome]=rea_tmp[atome]*reactant[1][num]
                        else :
                            rea_dict[atome]=rea_dict[atome]+rea_tmp[atome]*reactant[1][num]

            for num,prod in enumerate(product[0]) :
#                 print(prod, num, product)
                if prod != 'hv' :
                    prod_tmp=self.therm[prod].atomic_composition
                    # print(self.therm[prod].atomic_composition)
                    for atome in prod_tmp :
                        if atome not in prod_dict :
                            prod_dict[atome]=prod_tmp[atome]*product[1][num]
                        else :
                            prod_dict[atome]=prod_dict[atome]+prod_tmp[atome]*product[1][num]
            
            
            balance_error=False
            if rea_dict != prod_dict :
                is_different=False
                for atome in rea_dict :
                    # print(reaction.print_reaction())
                    # print(prod_dict)
                    try :
                        if rea_dict[atome]*0.99 >= prod_dict[atome] or rea_dict[atome] <= 0.99*prod_dict[atome] :
                            is_different=True
                            balance_error=True
                    except KeyError :
                        reaction.print_reaction()
                        print(rea_dict, prod_dict)
                        raise
                if is_different==True :
                    print('ERREUR : ', rea_dict, prod_dict)
                    print(reaction.__dict__)
                # else : 
                #     print('Rounded : ', rea_dict, prod_dict, reaction.__dict__)
            if balance_error==True :
                print(f'\n{"#"*100}\n{"#"*35} FATAL ERROR IN ATOMS BALANCE {"#"*35}\n{"#"*100}')
                reaction.print_reaction()
                raise Exception('FATAL ERROR IN ATOMS BALANCE')
            # print(sorted([x+str(int(rea_dict[x])) for x in rea_dict]))
            order=sorted([x+'@'+str(int(rea_dict[x])) for x in rea_dict], key=lambda item: ['c', 'h', 'n', 'p', 'o','s','f','cl', 'ar','he'].index(item.split('@')[0]))
            order=[x.replace('@','') for x in order]
            iso=''.join(order)
            if iso in iso_reactions : 
                iso_reactions[iso].append(reaction)
            else :
                iso_reactions[iso] = [reaction]
            reaction.iso=iso
        return(iso_reactions)
                
    def micro_mech(self, list_species) :
        reaction_list=[]
        inreaction_species=[]
        for species in list_species :
            for reaction in self.reactions[2] :
                sperea=[*reaction.species[0], *reaction.species[1]]
                if species in sperea  :
                    if reaction not in reaction_list :
                        reaction_list.append(reaction)
                    
                        for spe in sperea :
                            if spe not in inreaction_species :
                                inreaction_species.append(spe)
        return [inreaction_species, copy.deepcopy(reaction_list)]
        
    # def update(self):
    #     self.elem = self.reactions[0]
    #     self.spe = self.reactions[1]
    #     self.rea = self.reactions[2]
    
    # @property
    # def reactions(self):
    #     return self._reactions

    # @reactions.setter
    # def reactions(self, value):
    #     if value[2] != self._reactions[2]:
    #         # If the third element changes, update the second element
    #         value[1]=self.clear_species()
    #     self._reactions = value
        
            
    
    def clear_species(self, value):
        spe_set = set()

        for rea in value :
            for spe in [*rea.species[0], *rea.species[1]]:
                spe_set.add(spe)
        
        spe_remove=set()
        
        print(f'Before removing unused species : {len(self.spe)} species')
        for spe in copy.deepcopy(self.reactions[1]):
            if spe not in spe_set and spe not in ['he', 'ar', 'ne', 'n2']+[x for x in self.coll_species]:
                spe_remove.add(spe)
                self.therm.pop(spe)
                if hasattr(self, "trans") :
                    self.trans.pop(spe)
                self.spe_model.pop(spe)
        new_value=[x for x in self.reactions[1] if x not in spe_remove]
        print(f'Number of spe removed when reading the mech : {len(spe_remove)},\n{spe_remove}\nNew number of species : {len(self.spe)} species')
        return new_value
        
    
    @property
    def rea(self):
        return self.reactions[2]
    
    @rea.setter
    def rea(self, value):
        self.reactions[2] = value
        # Upon setting a new value for rea, update spe accordingly
        self.reactions[1] = self.clear_species(value)
            
    @property
    def spe(self):
        return self.reactions[1]
    
    @spe.setter
    def spe(self, value):
        self.reactions[1] = value
        self.isomer_groups = self.get_isomers(value)
            
    @property
    def elem(self):
        return self.reactions[0]
    
    @elem.setter
    def elem(self, value):
        self.reactions[0] = value
        
    def extract(self, species) :
        list_rea=[]
        set_spe=set()
        for rea in self.rea :
            comp=[*rea.species[0], *rea.species[1]]
            if any(x in comp for x in species) :
                list_rea.append(rea)
            
        for rea in list_rea :
            comp=[*rea.species[0],*rea.species[1]]
            for spe in comp :
                
                set_spe.add(spe)
        return list_rea, list(set_spe)
    
    def NASA_to_therm(self,NASA,base_temp) :
        NASA=NASA.split('\n')
        lim=3
        for idx,line in enumerate(NASA) :
            if lim > 3 and lim-idx==3:
                print(f'Additional atome in NASA polynomial line {idx+1}')
                continue
            print(line, lim, idx)
            if line[79]=='1' :
                if len(line.split('!')[0].strip()) > 80 :
                    additional_data=True
                else :
                    additional_data=False
                    
                species=line.strip()[:line.strip().index(' ')]
        
                hidden_formula=line[24:44]
                # hidden_formula+=line[73:78]
                hidden_formula=re.sub(r'\.',' ',hidden_formula)
                hidden_formula=[hidden_formula[x:x+5] for x in range(0,len(hidden_formula),5)]
                test_added_atoms_1=[line[73:75].strip(), line[75:78].strip()]
                # print(test_added_atoms_1)

                if test_added_atoms_1[0] != '' and test_added_atoms_1[0].isalpha() :
                    if test_added_atoms_1[1] != '' and test_added_atoms_1[1].isdigit():
                        if int(test_added_atoms_1[1]) != 0 :
                           test_added_atoms_1=([test_added_atoms_1[0], int(test_added_atoms_1[1])])
                        else :
                            test_added_atoms_1=[]
                    else :
                        test_added_atoms_1=[]
                else :
                    test_added_atoms_1=[]
                    
                for num,atomedata in enumerate(hidden_formula) :
                    hidden_formula[num]=atomedata.strip()
        
                hidden_formula=set(hidden_formula)
                hidden_formula=list(hidden_formula)
        
                if '0' in hidden_formula or '00' in hidden_formula :
                    hidden_formula=list(filter(lambda a: a != '0' and a != '00', hidden_formula))
        
                if '' in hidden_formula :
                    hidden_formula=list(filter(lambda a: a != '', hidden_formula))
        
                tmp_elements_list={}
                
                # print('HD :',hidden_formula)
                
                for num,atome in enumerate(hidden_formula) :
                    element=atome.split()[0]
                    # print('atome :',atome, hidden_formula)
                    if (len(hidden_formula) == 1 and len(atome) == 1) or atome.split()[1] == '0':
                        continue
                    else :
                        nb=atome.split()[1]
                        tmp_elements_list[element]=int(nb)
        
            
        
            #### actual temp integration
                test_temp=0
                actual_temp=line[45:73].split()
                # print(actual_temp,line)
                # actual_temp_2=line[45:73].split()
                test_added_atoms_2=[]
                test_added_atoms_1=[]

                if additional_data == True :
                    if line[80] == '&' :
                        lim+=1
                        change_line=True
                        added=1
                        line_ad=NASA[added].split('!')[0].strip()
                        # line_ad=purged_therm[index_line][0]
                        matches = re.findall(r'([A-Za-z])\s*(\d+)', line_ad)
                        test_added_atoms_2 = {}
                        for letter, num in matches:
                            test_added_atoms_2[letter] = int(num)
                        
                        while '&' in line_ad :
                            lim+=1
                            added+=1
                            line_ad=NASA[added].split('!')[0].strip()
                            matches = re.findall(r'([A-Za-z])\s*(\d+)', line_ad)
                            for letter, num in matches:
                                test_added_atoms_2[letter] = int(num)
                            
                       
                    else :
                        change_line=False
                        test_added_atoms_2=[line[x:x+5] for x in range(80,80+len(line[80:]),5)]
                        if len(test_added_atoms_2[-1])<3 :
                            test_added_atoms_2=test_added_atoms_2[:-1]
                        test_added_atoms_2=[[x[:2].strip(),x[2:].strip()] for x in test_added_atoms_2]
                        for atomedata in copy.deepcopy(test_added_atoms_2) :
                            if atomedata[0] != '' and atomedata[0].isalpha() :
                                if atomedata[1] != '' and atomedata[1].isdigit():
                                    if int(atomedata[1]) != 0 :
                                       test_added_atoms_2.remove(atomedata)
                                       test_added_atoms_2.append([atomedata[0], int(atomedata[1])])
                                    else :
                                        test_added_atoms_2.remove(atomedata)
                                else :
                                    test_added_atoms_2.remove(atomedata)
                            else :
                                test_added_atoms_2.remove(atomedata)
                                
                        test_added_atoms_2={x : y for (x,y) in test_added_atoms_2}
                        
                    
                for num,atomedata in enumerate(hidden_formula) :
                    hidden_formula[num]=atomedata.strip()
                
                if test_added_atoms_1 != [] :
                    if test_added_atoms_1[0] in tmp_elements_list :
                        tmp_elements_list[test_added_atoms_1[0]]+=test_added_atoms_1[1]
                    else :
                        tmp_elements_list[test_added_atoms_1[0]]=test_added_atoms_1[1]
                if test_added_atoms_2 != [] :
                    # print(test_added_atoms_2)
                    for new_atoms in test_added_atoms_2 :
                        if new_atoms in tmp_elements_list :
                            tmp_elements_list[new_atoms]+=test_added_atoms_2[new_atoms]
                        else :
                            tmp_elements_list[new_atoms]=test_added_atoms_2[new_atoms]
                
                actual_temp=list(map(float, actual_temp))
                actual_temp=sorted(actual_temp)
                
                if len(actual_temp) == 2 :
                    test_temp=actual_temp.copy()
                    actual_temp.append(base_temp[1])
                    
                elif len(actual_temp) == 0 :
                    actual_temp=base_temp.copy()
                    
                elif len(actual_temp) == 1 : 
                    print(f'ERROR : TOO FEW THERMO TEMPERATURE {len(actual_temp)} FOR {species}')
                actual_temp=sorted(actual_temp)
                
                if actual_temp[1]-actual_temp[0]<300 or actual_temp[2]-actual_temp[1]<500 :
                    print(f'Thermo temperature diff too low !!! : {species}'\
                          f' {actual_temp[1]-actual_temp[0]}, {actual_temp[2]-actual_temp[1]}'\
                          , actual_temp, test_temp)
                    
                split_nasa=[]
        
            #### NASA reading
            
        
            elif idx==lim :
                line_2=line[:60]
                line_2=re.sub('e 0', 'e+0', line_2)
                split_nasa=split_nasa+[float(line_2[x:x+15]) for x in range(0, len(line_2), 15)]
                if len(split_nasa) != 14 : print('SPLIT NASA LENGTH = ', len(split_nasa))
                return Thermo(species, tmp_elements_list, actual_temp, split_nasa, comment='')
                # all_thermo[species]=(Thermo(species, tmp_elements_list, actual_temp, split_nasa))
            else :
                line_2=line[:75]
                line_2=re.sub('e 0', 'e+0', line_2)
                split_nasa=split_nasa+[float(line_2[x:x+15]) for x in range(0, len(line_2), 15)]
                
    def get_isomers(self):
        isomer_groups={}
        for spe in self.spe:
            ato_comp=self.therm[spe].atomic_composition
            ato_comp=tuple(sorted(ato_comp.items()))
            if ato_comp in isomer_groups :
                isomer_groups[ato_comp].append(spe)
            else :
                isomer_groups[ato_comp]=[spe]
        
        return isomer_groups
                
    
    def isomers(self, formula):
        formula=formula.lower()
        two_letter_elements = {'he', 'ar', 'cl', 'ne', 'li', 'be', 'na', 'mg', 'al', 'si'}
        element_counts = {}

        pattern_two_letter = r'(' + '|'.join(two_letter_elements) + r')(\d*)'
        matches_two_letter = re.findall(pattern_two_letter, formula)
    
        for element, count in matches_two_letter:
            count = int(count) if count else 1
            if element in element_counts:
                element_counts[element] += count
            else:
                element_counts[element] = count
    
        for element, _ in matches_two_letter:
            formula = formula.replace(element, '', 1)
    
        pattern_single_letter = r'([a-z])(\d*)'
        matches_single_letter = re.findall(pattern_single_letter, formula)
    
        for element, count in matches_single_letter:
            count = int(count) if count else 1
            if element in element_counts:
                element_counts[element] += count
            else:
                element_counts[element] = count
    
        elements = list(element_counts.items())
    
        elements_sorted = sorted(elements, key=lambda x: x[0])
    
        return self.isomer_groups[tuple(elements_sorted)]
    
                
class Thermo :
    def __init__(self, species, atomic_composition, temp_list, nasa_list, comment, from_model='') :
        self.species=species
        self.atomic_composition=atomic_composition
        self.temp_list=temp_list
        self.nasa_list=nasa_list
        self.comment = comment
        self.from_model = from_model

    def __repr__(self):
        return self.species
    
    def raw_formula(self) :
        raw=''
        ato=self.atomic_composition
        priority_order = ['c', 'h', 'f', 'o', 's', 'n', 'p']
        for atom in priority_order:
            if atom in ato:
                if len(atom) == 1:  
                    raw += atom.upper() + (str(ato[atom]) if ato[atom] > 1 else '')
                else :
                    raw += atom[0].upper()+atom[1] + (str(ato[atom]) if ato[atom] > 1 else '')
        other_atoms = sorted(a for a in ato if a not in priority_order)
        for atom in other_atoms:
            if len(atom) == 1: 
                raw += atom.upper() + (str(ato[atom]) if ato[atom] > 1 else '')
            else :
                raw += atom[0].upper()+atom[1] + (str(ato[atom]) if ato[atom] > 1 else '')
        # if 'c' in ato :
        #     if ato['c'] > 1 :
        #         raw+='C'+str(ato['c'])
        #     else :
        #         raw+='C'
        # if 'h' in ato :
        #     if ato['h'] > 1 :
        #         raw+='H'+str(ato['h'])
        #     else :
        #         raw+='H'
        # if 'o' in ato :
        #     if ato['o'] > 1 :
        #         raw+='O'+str(ato['o'])
        #     else :
        #         raw+='O'
        # if 'n' in ato :
        #     if ato['n'] > 1 :
        #         raw+='N'+str(ato['n'])
        #     else :
        #         raw+='N'
        # if 'he' in ato :
        #     if ato['he'] > 1 :
        #         raw+='He'+str(ato['he'])
        #     else :
        #         raw+='He'
        # if 'ar' in ato :
        #     if ato['ar'] > 1 :
        #         raw+='Ar'+str(ato['ar'])
        #     else :
        #         raw+='Ar'
        return(raw)
    
    
    def molecular_mass(self) :
        ato=self.atomic_composition
        all_mass={'c':12.011, 'h':1.00784, 'o':15.999, 'f':18.998403, 'p':30.973762,'s':32.065, 'n':14.0067 ,
              'cl':35.453, 'he':4.002602, 'ne': 20.1797, 'ar':39.948}
        mass = 0
        for atom, count in ato.items() :
            mass+=all_mass[atom]*count
        return mass
    """-------------------------------------------------------------------------
                       NASA COMPUTED THERMODYNAMIC FUNCTIONS
    -------------------------------------------------------------------------"""
    
    def cp(nasa_coeffs, temp):
        a = nasa_coeffs
        t = temp
        return a[0] + a[1]*t + a[2]*t**2 + a[3]*t**3 + a[4]*t**4

    def h(nasa_coeffs, temp):
        a = nasa_coeffs
        t = temp
        return a[0] + a[1]*t/2 + a[2]*t**2/3 + a[3]*t**3/4 + a[4]*t**4/5 + a[5]/t

    def s(nasa_coeffs, temp):
        a = nasa_coeffs
        t = temp
        return a[0]*np.log(t) + a[1]*t + a[2]*t**2/2 + a[3]*t**3/3 + a[4]*t**4/4 + a[6]
    
    def calc_therm(self, f):
        n=500
        low_temps = np.linspace(self.temp_list[0], self.temp_list[1], n)
        high_temps = np.linspace(self.temp_list[1], self.temp_list[2], n)
        high_temp_f = f(self.nasa_list[:7], high_temps)
        low_temp_f = f(self.nasa_list[7:], low_temps)
        return np.hstack((low_temps, high_temps)), np.hstack((low_temp_f, high_temp_f))
    
    def G(self):
        temp, a = self.calc_therm(Thermo.s)
        temp, b = self.calc_therm(Thermo.h)
        return temp, a - b
    
    def new_calc_therm(self, temp, f):
        if self.temp_list[1]<temp[0] :
            if len(temp) != 2 :    
                print(f'Could happend with other, len(temp) should be 2 : {len(temp)}')
            mid_temp_index = 0
        else :
            mid_temp_index = np.argmin(np.abs(temp - self.temp_list[1]))
        high_temps = temp[mid_temp_index:]
        low_temps = temp[:mid_temp_index]
        high_temp_cp = f(self.nasa_list[:7], high_temps)
        if mid_temp_index != 0 :
            low_temp_cp = f(self.nasa_list[7:], low_temps)
            return np.hstack((low_temp_cp, high_temp_cp))
        else :
            return np.hstack((high_temp_cp))
    
    def G_new(self, temp):
        return self.new_calc_therm(temp, Thermo.s) - self.new_calc_therm(temp, Thermo.h)
    
    def plot_data(self) :
        # n=350
       
        T,data_cp= self.calc_therm(Thermo.cp)
        T,data_h= self.calc_therm(Thermo.h)
        T,data_s= self.calc_therm(Thermo.s)
        h_dif=[Thermo.h(self.nasa_list[7:], 298)*1.987*298, Thermo.h(self.nasa_list[7:], 500)*1.987*500, Thermo.h(self.nasa_list[7:], 700)*1.987*700]
        hf298=Thermo.h(self.nasa_list[7:], 298)*1.987*298
        s298=Thermo.s(self.nasa_list[7:], 298)*1.987
        cp_range=[298,500,1000,1500,2000]
        tlimit=self.temp_list[1]
        cp_values=[Thermo.cp(self.nasa_list[7:], x)*1.987 if x<tlimit else Thermo.cp(self.nasa_list[:7], x)*1.987 for x in cp_range]
        true_cp=[x for x in data_cp]
        true_h=[x*1.987*t for x,t in zip(data_h,T)]
        true_s=[x*1.987 for x in data_s]
        true_g=[h-t*s for h,t,s in zip(true_h,T,true_s)]
        true_hk=[x/1000 for x in true_h]
        true_mg10k=[-x/10000  for x in true_g]
        return {'T':T, 'cp/R':data_cp,
                'h/RT':data_h, 's/R':data_s, 'h_value':h_dif, 'cp' : true_cp,
                'h' : true_h, 's' : true_s, 'g' : true_g, 'hk' : true_hk, 'mg10k' : true_mg10k, 'hf298':hf298, 's298':s298, 'cp_values' :cp_values }
    
    def add_plot(self, fig, ax, nb) :
        # n=350
        colors = [
        "#1F77B4",
        "#D62728",# blue
        "#2CA02C",  # green
          # red
        "#9467BD",  # purple
        "#8C564B",  # brown
        "#E377C2",  # pink
        "#7F7F7F",  # gray
        "#17BECF",  # cyan
        "#BCBD22",  # olive/yellow-green
        ]
        color=colors[nb]
        
        T,data_cp= self.calc_therm(Thermo.cp)
        T,data_h= self.calc_therm(Thermo.h)
        T,data_s= self.calc_therm(Thermo.s)
        h_dif=[Thermo.h(self.nasa_list[7:], 298)*1.987*298, Thermo.h(self.nasa_list[7:], 500)*1.987*500, Thermo.h(self.nasa_list[7:], 700)*1.987*700]
        
        true_cp=[x*1.987 for x in data_cp]
        true_h=[x*1.987*t for x,t in zip(data_h,T)]
        true_s=[x*1.987 for x in data_s]
        true_g=[h-t*s for h,t,s in zip(true_h,T,true_s)]
        true_hk=[x/1000 for x in true_h]
        true_mg10k=[-x/10000  for x in true_g]
        ax.plot(T,true_mg10k, color=color, label = nb, alpha=0.7)
        ax.legend()
        ax.set_title(self.species)
        return {'T':T, 'cp/R':data_cp,
                'h/RT':data_h, 's/R':data_s, 'h_value':h_dif, 'cp' : true_cp,
                'h' : true_h, 's' : true_s, 'g' : true_g, 'hk' : true_hk, 'mg10k' : true_mg10k}
        


class Reactions :
    def __init__(self, species, coef, is_rev, speed, supinfo, third_body, comment, reaction_types, identifier, from_model, model, iso=0) :
        self.species = species
        self.coef = coef
        self.is_rev = is_rev
        self.speed = speed
        self.supinfo = supinfo
        self.third_body = third_body
        self.comment = comment
        self.reaction_types = reaction_types
        self.identifier=identifier
        self.from_model=from_model
        self.model=model
        self.iso=iso
    
    def __eq__(self, other) :
        # print(self, other)
        
        # def find_rea_rate :
        
        if isinstance(other, list) :
            try : 
                test=other[0].species
                other=other[0]
                # print('Object is a list of Reactions')
            except :
                raise Exception(f"FATAL ERROR : object is not a list {other}")
                
      
        comparison=[0,0,0,0,0,0,0,0,0]
        set1=set([*self.species[0],*self.species[1]])
        set2=set([*other.species[0],*other.species[1]])
        
        if set1 != set2 :
            comparison[0]=0
            return(False)
        else :
            tmp_set1=[set(x) for x in self.species]
            tmp_coef1=[set(x) for x in self.coef]
            tmp_set2=[set(x) for x in other.species]
            tmp_coef2=[set(x) for x in other.coef]
        if not((tmp_set1 == tmp_set2 or tmp_set1 == tmp_set2[::-1]) and (tmp_coef1 == tmp_coef2 or tmp_coef1==tmp_coef2[::-1])) :
            return(False)
        else :
            return(True)
   

          #WIP
            # if (tmp_set1 == tmp_set2 or tmp_set1 == tmp_set2[::-1]) and (tmp_coef1 == tmp_coef2 or tmp_coef1==tmp_coef2[::-1]) :
            #     comparison[0]=1
            #     if self.model==other.model :
            #         comparison[1]=1
            #     if self.identifier==other.identifier :
            #         comparison[2]=1
            #     if self.thrid_body==other.thrid_body :
            #         comparison[3]=1
            #     else :
            #         if self.third_body =='m' or other.third_body=='m' :
            #             comparison[3]='m'
            #         else :
            #             comparison[3]=2
            #     if 'duplicate' in self.reaction_types and 'duplicate' in other.reaction_types :
            #         comparison[4]=1
            #     if self.reaction_types==other.reaction_types :
            #         comparison[5]=1  
                
                
            # else :
            #     return(False)
            
            # if comparison[1] == 1 :
            #     if comparison[2] == 1 :
            #         return(True)
            #     elif comparison[3] == 0 :
                
                    
        
        #WIP
        
        if self.third_body == other.third_body :
            if (tmp_set1 == tmp_set2 or tmp_set1 == tmp_set2[::-1]) and (tmp_coef1 == tmp_coef2 or tmp_coef1==tmp_coef2[::-1])  :
                if self.is_rev != other.is_rev :
                    if self.model == other.model :
                        print('IMPORTANT WARNING : REV DIFFERENT IN SAME MECH !')
                        self.print_reaction()
                        other.print_reaction()
                        return(False)
                    else :
                        # print('REV DIFFERENT IN DIFFERENT MECH ! (so that you know, but it will be considered as the same reactions)')
                        # self.print_reaction()
                        # other.print_reaction()
                        return(True)
                    
                else :
                    if self.is_rev == False:
                        if tmp_set1 == tmp_set2[::-1] :
                            # print(f'REACTION != REVERSE REACTION : THAT IS THE EXCEPTION')
                            return(False)
                        elif tmp_set1 == tmp_set2 :
                            if self.model == other.model :
                                if 'duplicate' in self.reaction_types and 'duplicate' in other.reaction_types:
                                    if self.identifier == other.identifier :
                                        print('FALSE DUPLICATE')
                                        return(True)
                                    else : 
                                        # print('Duplicate')
                                        return(False)
                                else :
                                    if self.identifier == other.identifier :
                                        return(True)
                                    else :
                                        
                                        print(f'STRANGE REACTIONS : {self.identifier} {other.identifier}')
                                        self.print_reaction()
                                        other.print_reaction()
                                        return(False)#raise Exception('same rea with different duplicate ?')
                            else :
                                return(True)
                        else :
                            print('WTF ????????')
                    else :   
                        if self.model == other.model :
                            if 'duplicate' in self.reaction_types and 'duplicate' in other.reaction_types:
                                if self.identifier == other.identifier :
                                    print('FALSE DUPLICATE')
                                    return(True)
                                else : 
                                    #print('Duplicate')
                                    return(False)
                            else :
                                if self.identifier == other.identifier :
                                    return(True)
                                else :
                                    
                                    print('STRANGE REACTIONS :')
                                    self.print_reaction()
                                    other.print_reaction()
                                    return(True)
                                    # raise Exception('same rea with different duplicate ?')
                        else :
                            return(True)
            
            else :
                if tmp_set1 == tmp_set2 or tmp_set1 == tmp_set2[::-1] :
                    print('MAYBE FATAL ERROR, LOOK : ')
                    self.print_reaction()
                    other.print_reaction()
                    raise Exception('same rea ?')
                return(False)
        else :
            return(False)
        
    def species_x_coefs(self, flat=False) :
        coef=self.coef
        spe=self.species
        new_species=[]
        for sous_liste1, sous_liste2 in zip(spe, coef):
            temp = []
            # Boucle sur les éléments de la sous-liste 1 et leur nombre correspondant dans la sous-liste 2
            for elem1, mult in zip(sous_liste1, sous_liste2):
                # Répétition de l'élément autant de fois que spécifié
                if int(mult) != mult :
                    print(mult)
                temp.extend([elem1] * int(mult))
            # Ajout de la liste temporaire à la liste résultat
            new_species.append(temp)
        if flat==True :
            return [*new_species[0],*new_species[1]]
        else :
            return new_species
        
    def flat_species(self) :
        return [*self.species[0], *self.species[1]]
    
    def eq_rea(self, other) :
        if self.model == other.model :
            if self.identifier == other.identifier :
                return(True)
            else :
                return(False)
        else :
            raise Exception('eq_rea is used to search the reaction in the model')
            
    def print_reaction(self, path='', pr=True, max_len_name='', add_origin = True, return_str=False) :
        if self.is_rev == True :
            equal= '='
        elif self.is_rev == False :
            equal= '=>'
        else :
            print(f'ERROR, NO REV {self.__dict__}')

        if self.third_body != 0 :
            tb=f"+{self.third_body}"
            if self.supinfo != [] :
                low_check=["low/" for x in self.supinfo if 'low/' in x or 'low /' in x]
                tcheb_check=["tcheb/" for x in self.supinfo if 'tcheb/' in x or 'tcheb /' in x]
                if len(low_check) >= 1 or len(tcheb_check) >= 1 :
                    tb=f"(+{self.third_body})"
        else :
            tb=''

        reactant=[]
        product=[]
        # print(reaction.speed[1])
        for s, c in zip(self.species[0], self.coef[0]) :
            if c == 1 :
                c=''
            elif int(c) == c :
                c=int(c)
            reactant.append(str(c) + str (s))

        for s, c in zip(self.species[1], self.coef[1]) :
            if c == 1 :
                c=''
            elif int(c) == c :
                c=int(c)
            product.append(str(c) + str (s))

        final_reaction=f'{"+".join(reactant)}{tb if tb!= "" else ""}{equal}{"+".join(product)}{tb if tb!= "" else ""}'
        # to_write=f'{final_reaction:48} {reaction.speed[0]}{reaction.speed[1]:<+7.3f}{reaction.speed[2]:+11.3e}'
        # to_write='{:<48}{:>+12.3e}{:>+10.2E}{:>+10.1f}'.format\
        n_format=':>+9.3F'
        ea_format=':>+11.1f'
        if abs(self.speed[1])>=1000 :
            n_format=':>+10.2e'
            ea_format=':>+10.1f'
        if abs(self.speed[2])>1e7 :
            if ea_format==':>+10.1f' :
                ea_format=':>+10.2e'
            else :
                ea_format=':>+11.2e'
                
        
        to_write=f'{{:<48}}{{:>+12.3e}}{{{n_format}}}{{{ea_format}}}'.format\
        (final_reaction, self.speed[0], self.speed[1], self.speed[2])

        if len(to_write)>80 :
            print(f'Reaction from base model too big ! :\n{to_write}')
            to_write=re.sub(r"\s+", " ", to_write)
            # print(to_write)
        if pr is True :
            print((to_write).upper())
            
        # print(to_write,len(to_write))
            for sup in self.supinfo :
                print(('\t'+sup).upper())
        
        if path != '' :
            reaction_com = self.comment
            if '*:_:*' in reaction_com :
                reaction_com = reaction_com.split('*:_:*')[2]
            # reaction_com = reaction_com      
            a_o=f'*:_:*{self.from_model if self.from_model != "" else self.model:^{max_len_name+2 if max_len_name != "" else 20}}*:_:*' if add_origin==True else ''
            new_write=f'{to_write}\t! {a_o} {reaction_com}\n'
            for sup in self.supinfo :
                new_write+=(f'\t{sup}\n')
            if path=='return' :
                return (new_write).upper()
            
            else :
                with open(path, 'a') as extract :
                    extract.write(new_write.upper())
        if return_str==True :
            if path == '' :
                reaction_com = self.comment
                if '*:_:*' in reaction_com :
                    reaction_com = reaction_com.split('*:_:*')[2]
                a_o=f'*:_:*{self.from_model if self.from_model != "" else self.model:^{max_len_name+2 if max_len_name != "" else 20}}*:_:*' if add_origin==True else ''
                new_write=f'{to_write}\t! {a_o} {reaction_com}\n'
                for sup in self.supinfo :
                    new_write+=(f'\t{sup}\n')
            return new_write.upper()
            
    def prs(self) :
        
        return self.print_reaction(return_str=True, pr=False)
        
class Transport :
    def __init__(self, species, geo, lj_p, lj_cd, dp, p, rr, comment) :
        self.species = species
        self.geo = geo
        self.lj_p = lj_p
        self.lj_cd = lj_cd
        self.dp = dp
        self.p = p
        self.rr = rr
        self.comment = comment
        
