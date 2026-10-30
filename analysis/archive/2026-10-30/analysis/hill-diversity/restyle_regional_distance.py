"""Style the existing regional distance chart from its saved summary table."""
from pathlib import Path
from collections import Counter,defaultdict
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from figure_style import apply_style,TEAL,ORANGE,GRAY,PALETTE,ORDER_HATCHES
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'analysis/scripts/07-summary-tables-figures/output'
with (BASE/'species_by_order_family_distance.csv').open() as f:rows=list(csv.DictReader(f))
bins=['0 km (inside)','0-1 km','1-5 km','5-10 km','10-25 km','25-50 km','50+ km']
counts=defaultdict(Counter)
for r in rows:
 if r['order']=='TOTAL':continue
 for b in bins:counts[r['order']][b]+=int(r[b])
assert sum(sum(v.values()) for v in counts.values())==int(next(r['Total'] for r in rows if r['order']=='TOTAL'))
orders=sorted(counts,key=lambda k:(-sum(counts[k].values()),k))
keep=orders[:8];other=Counter()
for o in orders[8:]:other.update(counts[o])
if other:counts['Other']=other;keep+=['Other']
colors=[PALETTE[i % len(PALETTE)] for i in range(len(keep))]
apply_style()
fig,ax=plt.subplots(figsize=(10,7.5))
n=len(keep);width=.84/n
for i,(o,color) in enumerate(zip(keep,colors)):
 xs=[x-.42+(i+.5)*width for x in range(len(bins))]
 ax.bar(xs,[counts[o][b] for b in bins],width=width*.9,color=color,label=o,hatch=ORDER_HATCHES[i],edgecolor='white',linewidth=.3)
ax.set_xticks(range(len(bins)),['Inside','0–1','1–5','5–10','10–25','25–50','50+'])
ax.set(xlabel='Distance to preserve boundary (km)',ylabel='Number of species',title='Regional arthropod species by order and distance')
ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.20),ncols=3,fontsize=12,frameon=False)
fig.subplots_adjust(left=.12,right=.98,top=.9,bottom=.34)
for ext in ['png','pdf','svg']:fig.savefig(BASE/f'species_by_order_and_distance.{ext}',dpi=250,facecolor='white')
print('Restyled regional distance chart; saved table and counts unchanged.')
