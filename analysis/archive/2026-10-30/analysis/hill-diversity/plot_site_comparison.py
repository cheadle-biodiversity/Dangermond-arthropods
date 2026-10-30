"""Observed Hill profiles for the complete insect survey and its two named sites."""
from pathlib import Path
from collections import Counter
import csv
import math
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/hill-diversity/2026-10-27-insects'
from figure_style import apply_style, format_color, TEAL, ORANGE, GRAY
apply_style()
COLORS = [TEAL, ORANGE, GRAY]


def diversity(names, q):
    counts = Counter(names)
    p = [n/sum(counts.values()) for n in counts.values()]
    if q == 0:return len(counts)
    if abs(q-1)<1e-9:return math.exp(-sum(x*math.log(x) for x in p))
    return sum(x**q for x in p)**(1/(1-q))


def draw(ax, groups, title, limit):
    qs = [i/100 for i in range(201)]
    for label, rows in groups:
        color = format_color(label)
        names = [r['analysis_taxon_name'] for r in rows]
        ys=[diversity(names,q) for q in qs]
        display_label = label.replace("Perko's", 'Perco’s')
        ax.plot(qs,ys,color=color,lw=3,label=f'{display_label} (n = {len(rows)})')
        values = [diversity(names,q) for q in [0,1,2]]
        ax.scatter([0,1,2],values,color=color,s=40,zorder=3)
        if len(groups)==2:
            for q,y in zip([0,1,2],values):ax.annotate(f'{y:.1f}'.removesuffix('.0'),(q,y),xytext=(0,8),textcoords='offset points',ha='center',fontsize=13,color=color)
    ax.set(title=title,xlim=(-.08,2.08),ylim=(0,limit),ylabel='Effective number of species',xlabel='Diversity order (q)')
    ax.set_xticks([0,1,2],['0\nRichness','1\nShannon','2\nInverse\nSimpson'])
    ax.grid(axis='y',alpha=.16)
    ax.legend(frameon=True,framealpha=.95,edgecolor='none',loc='upper right',fontsize=12)


def save(fig,stem):
    for ext in ['png','pdf','svg']:
        fig.savefig(OUT/f'{stem}.{ext}',dpi=250,facecolor='white')
    plt.close(fig)


rows=list(csv.DictReader((OUT/'site_record_audit.csv').open()))
fig,axes=plt.subplots(2,1,figsize=(8.5,8.5),gridspec_kw={'height_ratios':[1.3,1]})
sites=["Perko's Beach",'Lighthouse backdunes']
groups=[(site,[r for r in rows if r['site_group']==site]) for site in sites]
draw(axes[0],groups,'A. Overall observed diversity',55)
sets=[{r['analysis_taxon_name'] for r in rs} for _,rs in groups]
shared=sets[0]&sets[1];union=sets[0]|sets[1]
counts=[len(sets[0]-sets[1]),len(shared),len(sets[1]-sets[0])]
labels=["Perco’s only",'Shared','Backdunes only']
axes[1].barh([2,1,0],counts,color=[COLORS[0],COLORS[2],COLORS[1]],height=.58)
axes[1].set_yticks([2,1,0],labels)
axes[1].set(xlabel='Species-level units',xlim=(0,max(counts)+6),title='B. Shared and site-only units')
for y,n in zip([2,1,0],counts):axes[1].text(n+.5,y,str(n),va='center',fontsize=14)
fig.suptitle("Observed insect diversity\nPerco’s Beach and lighthouse backdunes",fontsize=17,y=.98)
fig.subplots_adjust(left=.22,right=.97,bottom=.19,top=.82,hspace=.85)
save(fig,'hill_site_comparison')
fig,ax=plt.subplots(figsize=(7.2,4.8))
groups=[('All records',rows),('Preserved specimens',[r for r in rows if r['basisOfRecord']=='PreservedSpecimen']),('Human observations',[r for r in rows if r['basisOfRecord']=='HumanObservation'])]
draw(ax,groups,'Observed insect diversity across Dangermond',70)
fig.subplots_adjust(left=.11,right=.97,bottom=.27,top=.9)
save(fig,'hill_survey_comparison')
print('Saved site and survey Hill profiles as PNG, PDF and SVG.')
