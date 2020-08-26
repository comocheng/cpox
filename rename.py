import os
import re
import glob
import sys

# array = os.listdir('./sensitivities-small-grid-copy/')
# files = ['./sensitivities-small-grid-copy/' + x for x in array]

for filename in glob.glob('sensitivities-small-grid-rename/*.pdf'):

    f = re.split('/', filename)
    title = f[1]

    title = re.sub(' CH4Conv ', 'CH4Conv', title)
    title = re.sub(' COSelec ', 'CoSelec', title)
    title = re.sub(' COYield ', 'CoYield', title)
    title = re.sub(re.escape(' FullOxSelec '), 'FullOxSelec', title)
    title = re.sub(re.escape(' FullOxYield '), 'FullOxYield', title)
    title = re.sub(' ExitT ', 'ExitTemp', title)
    title = re.sub(' H2Selec ', 'H2Selec', title)
    title = re.sub(' H2Yield ', 'H2Yield', title)
    title = re.sub(' MaxT ', 'MaxTemp', title)
    title = re.sub(' O2Conv ', 'O2Conv', title)
    title = re.sub(' SynGasSelec ', 'SynGasSelec', title)
    title = re.sub(' SynGasYield ', 'SynGasYield', title)
    title = re.sub(' DistToMaxT ', 'DistToMaxT', title)
    title = re.sub(' DistTo50CH4Conv ', 'DistTo50CH4Conv', title)
    title = re.sub(' MaxRateCH4Conv ', 'MaxRateCH4Conv', title)

    # removing decimal point, because latex doesn't like them
    search = re.search(r'\d\.\d', title)
    search = re.split('\.', search.group(0))
    title = re.sub(r'\d\.\d', str(search[0] + search[1]), title)

    title = re.sub(re.escape('[O][O] + 2 [Pt] <=> 2 O=[Pt]'), 'rxn1', title)
    title = re.sub(re.escape('[H][H] + 2 [Pt] <=> 2 [Pt]'), 'rxn2', title)
    title = re.sub(re.escape('[Pt] + O=[Pt] <=> O[Pt] + [Pt]'), 'rxn3', title)
    title = re.sub(re.escape('C + 2 [Pt] <=> C[Pt] + [Pt]'), 'rxn4', title)
    title = re.sub(re.escape('C + O=[Pt] + [Pt] <=> C[Pt] + O[Pt]'), 'rxn5', title)
    title = re.sub(re.escape('C=[Pt] + [Pt] <=> C[Pt] + [Pt]'), 'rxn6', title)
    title = re.sub(re.escape('C#[Pt] + [Pt] <=> C=[Pt] + [Pt]'), 'rxn7', title)
    title = re.sub(re.escape('C#[Pt] + [Pt] <=> C~[Pt] + [Pt]'), 'rxn8', title)
    title = re.sub(re.escape('C~[Pt] + [H][H] <=> C=[Pt]'), 'rxn9', title)
    title = re.sub(re.escape('[C-]#[O+] + [Pt] <=> O=C=[Pt]'), 'rxn10', title)
    title = re.sub(re.escape('C~[Pt] + O=[Pt] <=> O=C=[Pt] + [Pt]'), 'rxn11', title)
    title = re.sub(re.escape('C + O[Pt] + [Pt] <=> C[Pt] + O.[Pt]'), 'rxn12', title)
    title = re.sub(re.escape('O + [Pt] <=> O.[Pt]'), 'rxn13', title)
    title = re.sub(re.escape('O.[Pt] + O=[Pt] <=> 2 O[Pt]'), 'rxn14', title)
    title = re.sub(re.escape('O[Pt] + [Pt] <=> O.[Pt] + [Pt]'), 'rxn15', title)
    title = re.sub(re.escape('[Pt] + O[Pt] <=> O.[Pt] + [Pt]'), 'rxn15', title)
    title = re.sub(re.escape('O=C=O + [Pt] <=> O=C=O.[Pt]'), 'rxn16', title)
    title = re.sub(re.escape('O=C=[Pt] + O=[Pt] <=> O=C=O.[Pt] + [Pt]'), 'rxn17', title)
    title = re.sub(re.escape('O=C=O.[Pt] + [Pt] <=> O[Pt] + O=C=[Pt]'), 'rxn18', title)
    title = re.sub(re.escape('O=C=O.[Pt] + [Pt] <=> O=C=[Pt] + O[Pt]'), 'rxn18', title)
    title = re.sub(re.escape('C + [Pt] <=> C.[Pt]'), 'rxn19', title)
    title = re.sub(re.escape('[H][H] + [Pt] <=> [H][H].[Pt]'), 'rxn20', title)
    # title = re.sub(re.escape('[C-]#[O+] + [Pt] <=> [C-]#[O+].[Pt]'), 'rxn21', title)  # removed from model
    title = re.sub(re.escape('[H] + [Pt] <=> [Pt]'), 'rxn21', title)
    title = re.sub(re.escape('[OH] + [Pt] <=> O[Pt]'), 'rxn22', title)
    title = re.sub(re.escape('[CH3] + [Pt] <=> C[Pt]'), 'rxn23', title)
    title = re.sub(re.escape('[CH]=O + [Pt] <=> O=C[Pt]'), 'rxn24', title)
    title = re.sub(re.escape('O + 2 [Pt] <=> O[Pt] + [Pt]'), 'rxn25', title)
    title = re.sub(re.escape('O + 2 [Pt] <=> [Pt] + O[Pt]'), 'rxn25', title)
    title = re.sub(re.escape('CC + 2 [Pt] <=> 2 C[Pt]'), 'rxn26', title)
    title = re.sub(re.escape('CO + 2 [Pt] <=> C[Pt] + O[Pt]'), 'rxn27', title)
    title = re.sub(re.escape('C=O + 2 [Pt] <=> O=C[Pt] + [Pt]'), 'rxn28', title)
    title = re.sub(re.escape('CC=O + 2 [Pt] <=> C[Pt] + O=C[Pt]'), 'rxn29', title)
    title = re.sub(re.escape('C=[Pt] + O[Pt] <=> C[Pt] + O=[Pt]'), 'rxn30', title)
    title = re.sub(re.escape('C#[Pt] + O[Pt] <=> C=[Pt] + O=[Pt]'), 'rxn31', title)
    title = re.sub(re.escape('2 C=[Pt] <=> C[Pt] + C#[Pt]'), 'rxn32', title)
    title = re.sub(re.escape('C~[Pt] + O[Pt] <=> C#[Pt] + O=[Pt]'), 'rxn33', title)
    title = re.sub(re.escape('C[Pt] + C~[Pt] <=> C=[Pt] + C#[Pt]'), 'rxn34', title)
    title = re.sub(re.escape('C=[Pt] + C~[Pt] <=> 2 C#[Pt]'), 'rxn35', title)
    title = re.sub(re.escape('O=C[Pt] + O=[Pt] <=> O[Pt] + O=C=[Pt]'), 'rxn36', title)
    title = re.sub(re.escape('O=C[Pt] + O=[Pt] <=> O=C=[Pt] + O[Pt]'), 'rxn36', title)
    title = re.sub(re.escape('C=[Pt] + O=C[Pt] <=> C[Pt] + O=C=[Pt]'), 'rxn37', title)
    title = re.sub(re.escape('O=C[Pt] + C#[Pt] <=> C=[Pt] + O=C=[Pt]'), 'rxn38', title)
    title = re.sub(re.escape('O=C[Pt] + C~[Pt] <=> C#[Pt] + O=C=[Pt]'), 'rxn39', title)
    title = re.sub(re.escape('O=C[Pt] + [Pt] <=> [Pt] + O=C=[Pt]'), 'rxn40', title)
    title = re.sub(re.escape('O=C[Pt] + [Pt] <=> O=C=[Pt] + [Pt]'), 'rxn40', title)

    f = str(f[0] + '/' + title)
    os.rename(filename, f)
