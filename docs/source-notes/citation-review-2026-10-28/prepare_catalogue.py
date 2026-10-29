"""Prepare APA-style reference text; numbering is assigned from live first use."""
from pathlib import Path
import html,json,re

BASE=Path(__file__).resolve().parent
source=json.loads((BASE/'input_references.json').read_text())['references']
verified=json.loads((BASE/'doi_verification.json').read_text())

def initials(given):
    given=given.replace('‐','-').replace('‑','-')
    words=given.split()
    result=[]
    for word in words:
        if '-' in word:
            result.append('-'.join(p[0].upper()+'.' for p in word.split('-') if p))
        elif '.' in word:
            result.extend(x.upper()+'.' for x in re.findall(r'[A-Za-zÀ-ž]',word))
        elif word:result.append(word[0].upper()+'.')
    return ' '.join(result)

def authors(items):
    names=[]
    for item in items:
        family=item.get('family','')
        if family.isupper():family=family.title()
        if family.endswith(' Jr.'):
            family=family[:-4];suffix=', Jr.'
        else:suffix=''
        names.append(family+', '+initials(item.get('given',''))+suffix)
    if len(names)>20:return ', '.join(names[:19])+', . . . '+names[-1]
    if len(names)>1:return ', '.join(names[:-1])+', & '+names[-1]
    return ''.join(names)

# Article titles retain the reviewed spelling and scientific names in the draft.
journals={2:'Biological Conservation',3:'Ecological Entomology',4:'Biological Invasions',5:'Journal of Applied Entomology',7:'Journal of Animal Ecology',8:'Proceedings of the National Academy of Sciences',9:'Molecular Ecology Notes',10:'PLOS ONE',11:'Insect Conservation and Diversity',12:'Ecology',13:'ZooKeys',16:'Ecological Entomology',17:'European Journal of Entomology',19:'Estuarine, Coastal and Shelf Science',22:'Journal of the Kansas Entomological Society',23:'The Great Lakes Entomologist',24:'The Coleopterists Bulletin',25:'Transactions of the San Diego Society of Natural History',26:'Estuarine, Coastal and Shelf Science',28:'Annals of the Entomological Society of America',29:'ZooKeys',33:'Journal of Animal Ecology',34:'Insect Conservation and Diversity',39:'Ecological Monographs',41:'Global Ecology and Biogeography',42:'PLOS ONE',44:'Ecology and Evolution',46:'Behavioral Ecology',50:'Ecological Entomology',55:'Annual Review of Ecology, Evolution, and Systematics',56:'Proceedings of the Royal Society B: Biological Sciences',57:'Environmental Management',58:'Biodiversity Informatics',64:'Conservation Science and Practice',65:'Ecological Solutions and Evidence',66:'Annals of the Entomological Society of America',67:'Ecology'}
details={2:('127','3','319–326'),3:('49','5','739–743'),4:('22','','681–691'),5:('141','7','540–550'),7:('75','2','368–376'),8:('98','3','1095–1100'),9:('7','3','355–364'),10:('7','1','e29715'),11:('1','','222–232'),12:('51','6','1012–1017'),13:('384','','1–256'),16:('46','2','143–159'),17:('102','4','809–812'),19:('58','Supplement','25–40'),22:('75','1','3–7'),23:('7','4','Article 1'),24:('73','3','473–493'),25:('16','12','279–290'),26:('150','','67–75'),28:('61','5','1284–1299'),29:('728','','1–455'),33:('92','','1802–1814'),34:('18','6','1109–1119'),39:('84','1','45–67'),41:('23','1','99–112'),42:('8','7','e66213'),44:('12','3','e8505'),46:('37','4','arag054'),50:('42','6','731–736'),55:('45','','45–67'),56:('279','1727','266–274'),57:('54','','1249–1266'),58:('2','','1–10'),64:('7','5','e70016'),65:('7','1','e70173'),66:('117','4','220–233'),67:('93','12','2533–2547')}

manual={
1:'Griffith, G. E., Omernik, J. M., Johnson, C. B., & Turner, D. S. (2014). *Ecoregions of Arizona* [Poster; Open-File Report 2014–1141]. U.S. Geological Survey. https://doi.org/10.3133/ofr20141141',
6:'Matsuda, T., Brehme, C. S., & Fisher, R. N. (2015). *Assessing presence of Argentine ants using the bait method* [Survey protocol]. U.S. Geological Survey, Western Ecological Research Center. https://sdmmp.com/upload/SDMMP_Repository/0/vgtn1f4x5dw9m0k2y6zcb83s7prqh.pdf',
14:'University of California, Riverside, Center for Invasive Species Research. (n.d.). *Red bug: Scantius aegyptius*. Retrieved October 28, 2026, from https://cisr.ucr.edu/invasive-species/red-bug',
15:'Xerces Society. (n.d.). *Obscure bumble bee: Bombus caliginosus*. Retrieved October 28, 2026, from https://xerces.org/endangered-species/species-profiles/at-risk-bumble-bees/obscure-bumble-bee',
18:'California Conservation Genomics Project. (2026, August 28). *Trigonoscuta spp. (dune weevils)*. https://www.ccgproject.org/species/trigonoscuta-spp-dune-weevils',
20:'Dugan, J., & Marrifini, M. (2022). *California coast, ecosystem surveys of sandy beaches and surf zones August 2019–February 2020* [Data set]. California Ocean Protection Council Data Repository. https://doi.org/10.25494/P6989J',
21:'Dugan, J. E., Marraffini, M., Ladd, M., Hubbard, D. M., Hamilton, S., Marin-Jarrin, J., Colwell, M., Neuman, K., Lindquist, K., Robinette, D., Page, H. M., Madden, J., Koval, G., & Nielsen, K. J. (2022). *Evaluating performance of California’s MPA network through the lens of sandy beach and surf zone ecosystems* [Final report]. California Sea Grant. https://caseagrant.ucsd.edu/sites/default/files/FinalMPAReportBeachesSurfZones2022.pdf',
27:'Maddison, W. (1995). *Jumping spiders of America North of Mexico: Terralonus*. Tree of Life Web Project. https://tolweb.org/accessory/NA_Jumping_Spiders%3A_Terralonus?acc_id=2130',
30:'Perry, E. J. (2010, November). *Hoplia beetle* (Pest Notes, Publication 7499). University of California Statewide Integrated Pest Management Program. https://ipm.ucanr.edu/home-and-landscape/hoplia-beetle/',
31:'Sandoval, C. (2007, November 9). *Survey of globose dune beetle at 30732 Pacific Coast Highway (Broad Beach)* [Field report, Appendix B in Biological resources assessment]. California Coastal Commission. https://documents.coastal.ca.gov/reports/2008/6/W16a-6-2008-a1.pdf',
32:'Montana Natural Heritage Program, & Montana Fish, Wildlife & Parks. (n.d.). *Western tiger beetle: Cicindela oregona oregona*. Montana Field Guide. Retrieved October 28, 2026, from https://fieldguide.mt.gov/speciesDetail.aspx?elcode=IICOL02364',
35:'University of California Agriculture and Natural Resources. (n.d.). *What about honey bees?* The Pollinator Project. Retrieved October 28, 2026, from https://ucanr.edu/site/pollinator-project-pollinator-attractiveness-southern-california-ornamentals/what-about-honey?about=1',
36:'University of California Statewide Integrated Pest Management Program. (2009, February). *Eucalyptus tortoise beetles*. https://ipm.ucanr.edu/home-and-landscape/eucalyptus-tortoise-beetles/',
37:'World Spider Catalog. (2026). *Marinarozelotes barbatus (L. Koch, 1866)*. Natural History Museum Bern. Retrieved October 28, 2026, from https://www.wsc.nmbe.ch/spec-data/18743',
38:'AntWeb. (2026). *Cardiocondyla mauritanica: Specimen CASENT0724085* [Specimen record]. California Academy of Sciences. Retrieved October 28, 2026, from https://www.antweb.org/specimen/CASENT0724085',
40:'Cheadle Biodiversity. (2026). *Dangermond-arthropods: Analysis pipeline* [Computer software]. GitHub. Retrieved October 28, 2026, from https://github.com/cheadle-biodiversity/Dangermond-arthropods/tree/master/analysis',
43:'Knapp, D. A. (2014). *Effects of an exotic plant invasion on arthropod assemblages* [Doctoral dissertation, University of California, Santa Barbara]. Alexandria Digital Research Library. https://alexandria.ucsb.edu/downloads/mp48sd085',
45:'Koch, J., Strange, J., & Williams, P. (2012). *Bumble bees of the western United States*. U.S. Forest Service & Pollinator Partnership. https://www.ars.usda.gov/ARSUserFiles/20800500/BumbleBeeGuideWestern2012.pdf',
47:'California Department of Fish and Wildlife. (n.d.). *Invasive to avoid: Iceplant*. Retrieved October 28, 2026, from https://wildlife.ca.gov/Conservation/Plants/Dont-Plant-Me/Iceplant',
48:'California Invasive Plant Council. (2005). *Cotula coronopifolia: Plant assessment form*. https://www.cal-ipc.org/plants/paf/cotula-coronopifolia-plant-assessment-form/',
49:'California Invasive Plant Council. (n.d.). *Cakile maritima: Plant profile*. Retrieved October 28, 2026, from https://www.cal-ipc.org/plants/profile/cakile-maritima-profile/',
51:'GBIF.org. (2026, September 28). *GBIF occurrence download* [Data set]. https://doi.org/10.15468/dl.vgv5ee',
52:'GBIF Secretariat. (n.d.). *Taxonomy interpretation*. GBIF technical documentation. Retrieved October 28, 2026, from https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation',
53:'U.S. Environmental Protection Agency. (n.d.). *Ecoregion download files by region*. Retrieved October 28, 2026, from https://www.epa.gov/eco-research/ecoregion-download-files-region',
54:'Entomological Society of America. (n.d.). *Common names of insects database*. Retrieved October 28, 2026, from https://entsoc.org/publications/common-names',
59:'California Natural Diversity Database. (2026, October). *Special animals list*. California Department of Fish and Wildlife. https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=109406&inline=',
60:'U.S. Fish and Wildlife Service. (2026, September 21). *Save the monarch*. https://www.fws.gov/our-work/pollinators/save-monarch',
61:'Butterflies and Moths of North America. (n.d.). *Wandering skipper: Panoquina errans*. Retrieved October 28, 2026, from https://www.butterfliesandmoths.org/species/Panoquina-errans',
62:'Shanks, S. (n.d.). *Ammopelmatus muwu: Point Conception Jerusalem cricket* [Species account]. California Department of Fish and Game, Natural Diversity Database. https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=107616',
63:'Blecha, J., Cleveland, C., Innis, D., & Vogler, W. (2007). *Fauna of the Guadalupe-Nipomo Dunes*. Dunes Collaborative. https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=223918',
68:'Baxter, T. I., Walker, I. J., Dugan, J. E., Hubbard, D. M., Engeman, L., Emery, K. A., Vitousek, S., Johnston, K. K., Pickart, A. J., Smith, S., Fee, D. R., Willett, D., & Wisniewski, J. (2026). *California coastal dune inventory* [Data set]. Dryad. https://doi.org/10.5061/dryad.hqbzkh1w7',
69:'The Nature Conservancy. (n.d.). *Dangermond Preserve data portal* [Data portal]. DataONE. Retrieved October 28, 2026, from https://search.dataone.org/portals/tnc_dangermond',
70:'DataONE. (n.d.). *DataONE*. Retrieved October 28, 2026, from https://www.dataone.org/'
}

entries=[]
for key,original in enumerate(source):
    raw=original['text'].strip();v=verified[key];m=v.get('metadata',{}).get('message',{})
    if key==0:
        title=m['title'][0]
        formatted=f"{authors(m['author'])} (2025). *{title}* [Preprint]. Authorea. https://doi.org/{v['doi']}"
    elif key in manual:formatted=manual[key]
    elif key in journals:
        year=re.search(r'\b(19\d{2}|20\d{2})\b',raw).group()
        au=authors(m['author']) if m.get('author') else raw.split('('+year+')')[0].strip()
        if key==57:au='Omernik, J. M., & Griffith, G. E.'
        if key==10:au='Wieczorek, J., Bloom, D., Guralnick, R., Blum, S., Döring, M., Giovanni, R., Robertson, T., & Vieglais, D.'
        if key in (55,56,57,58):
            title=raw.split(year+'. ',1)[1]
        else:title=raw.split('('+year+'). ',1)[1]
        journal=journals[key]
        # Original titles are sentence case and preserve proper scientific names.
        aliases=[journal]
        if key in (10,42):aliases+=['PloS one','PLoS ONE']
        if key==56:aliases+=['Proceedings of the Royal Society B']
        title=next((title.split(j,1)[0].strip().rstrip('.') for j in aliases if j in title),title)
        if key==9:title='BOLD: The Barcode of Life Data System (www.barcodinglife.org)'
        volume,issue,pages=details[key]
        doi=v.get('doi','')
        if key==10:doi='10.1371/journal.pone.0029715'
        url='https://doi.org/'+doi if doi else (re.search(r'https?://\S+',raw).group().rstrip('.') if 'http' in raw else '')
        formatted=f"{au} ({year}). {title}. *{journal}, {volume}*"+(f'({issue})' if issue else '')+f', {pages}.'+(f' {url}' if url else '')
    else:raise RuntimeError(key)
    entries.append(dict(key=key,original=raw,formatted=formatted,verification=v['status'],doi=v['doi']))
for key in [68,69,70]:entries.append(dict(key=key,original='',formatted=manual[key],verification='primary source verified',doi=''))

def unwrap(text):
    plain='';italics=[];on=False;start=0
    for char in text:
        if char=='*':
            if on:italics.append(dict(start=start,end=len(plain)))
            else:start=len(plain)
            on=not on
        else:plain+=char
    assert not on
    return plain,italics

for e in entries:
    e['text'],e['italics']=unwrap(e['formatted'])
    e['urls']=re.findall(r'https?://\S+',e['text'])
    assert '…..' not in e['text']
(BASE/'reference_catalogue.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
print('Prepared',len(entries),'APA-style entries, including 3 missing sources.')
