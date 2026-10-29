"""Re-render archived figures with the approved survey label, using saved frequencies.
No filtering or changes to the archived numerical results.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/hill-diversity/2026-10-26'
def read(name):
 with (OUT/name).open(newline='') as f:return list(csv.DictReader(f))
series=defaultdict(Counter)
for r in read('taxon_record_frequencies.csv'):series[r['series']][r['taxon_key']]=int(r['records'])
qs=sorted({float(r['q']) for r in read('hill_profiles.csv')})
rar=[dict(series=r['series'],records=int(r['records']),expected_taxa=float(r['expected_taxa'])) for r in read('record_rarefaction.csv')]
def hill(c,q):
 p=[n/sum(c.values()) for n in c.values()]
 if q==0:return float(len(c))
 if abs(q-1)<1e-10:return math.exp(-sum(x*math.log(x) for x in p))
 return sum(x**q for x in p)**(1/(1-q))
def display(k):
 return k.replace('Perko’s', 'Perco’s').replace('Ecdysis: ', 'UCSB Summer 2026 survey: ')
from figure_style import apply_style, format_color, TEAL, ORANGE, GRAY
apply_style(scale=1.25)
colors=[TEAL,ORANGE,GRAY]
def plot_profile(ax,items,title,unit):
    for i,k in enumerate(items):
        c=series[k];ax.plot(qs,[hill(c,q) for q in qs],lw=3,color=format_color(k),label=f'{display(k)}\n{sum(c.values()):,} records; {len(c):,} taxa')
        ax.scatter([0,1,2],[hill(c,q) for q in [0,1,2]],color=format_color(k),s=40,zorder=3)
    ax.set(title=title,xlabel='Diversity order q',ylabel=unit,xticks=[0,1,2,3]);ax.grid(alpha=.16);ax.legend(frameon=False,fontsize=14)
fig,axs=plt.subplots(2,2,figsize=(14,10.5))
plot_profile(axs[0,0],['Ecdysis: named species','GBIF: named species assignments'],'A  Named-species profiles','Effective number of\nnamed species')
plot_profile(axs[0,1],['GBIF: barcode BINs'],'B  Barcode clusters','Effective number of\nbarcode BINs')
plot_profile(axs[1,0],['Ecdysis: orders','GBIF: orders'],'C  Broad taxonomic coverage','Effective number of orders')
ax=axs[1,1]
for i,k in enumerate(['Ecdysis: named species','GBIF: named species assignments']):
    a=[r for r in rar if r['series']==k];ax.plot([r['records'] for r in a],[r['expected_taxa'] for r in a],lw=3,color=format_color(k),label=display(k))
ax.set(title='D  Record rarefaction (q = 0)',xlabel='Number of occurrence records',ylabel='Expected number of\nnamed species');ax.grid(alpha=.16);ax.legend(frameon=False,fontsize=14)
fig.suptitle('Dangermond Preserve — Hill diversity curves',fontsize=22,fontweight='bold',y=.99)
fig.text(.5,.925,'UCSB Summer 2026 survey\nGBIF: saved preserve terrestrial-arthropod extract',ha='center',fontsize=15)
fig.tight_layout(rect=[0,.075,1,.86])
for ext in ['png','pdf','svg']:fig.savefig(OUT/f'Hill_diversity_overview.{ext}',dpi=220)
plt.close(fig)
fig,ax=plt.subplots(figsize=(10,6.5))
plot_profile(ax,['Ecdysis: Perko’s Beach, July','Ecdysis: lighthouse area, July'],'July 2026 — locality-specific named-species profiles','Effective number of\nnamed species')
fig.tight_layout(rect=[0,.09,1,1])
for ext in ['png','pdf','svg']:fig.savefig(OUT/f'Hill_profiles_Perkos_vs_lighthouse.{ext}',dpi=220)
plt.close(fig)

print('Updated survey labels in archived figures; source frequencies unchanged.')

for path in OUT.glob("*.svg"):
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
