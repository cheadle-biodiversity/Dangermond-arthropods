"""Shared colors and larger typography for the report's diversity graphs."""
import matplotlib.pyplot as plt
# Colors drawn from the report cover: foliage, insect cuticle, photo backgrounds.
TEAL = '#59784D'  # leaf green; legacy constant retained for importing scripts
ORANGE = '#9C502F'  # rust brown
GRAY = '#626B61'
DNA = '#6A7FA8'  # slate blue
TEXT = '#173C60'  # Cheadle Center navy
PALETTE = (TEAL, ORANGE, DNA, GRAY)
ORDER_HATCHES = ('', '', '', '', '//', '//', '//', '//', 'xx')

def apply_style(scale=1):
    plt.rcParams.update({
        'font.family':'Times','font.size':14*scale,
        'axes.titlesize':16*scale,'axes.titleweight':'bold',
        'axes.labelsize':14*scale,'xtick.labelsize':12*scale,
        'ytick.labelsize':12*scale,'legend.fontsize':12*scale,
        'text.color':TEXT,'axes.labelcolor':TEXT,
        'xtick.color':TEXT,'ytick.color':TEXT,
        'axes.spines.top':False,'axes.spines.right':False,
        'axes.prop_cycle':plt.cycler(color=PALETTE),
        'svg.fonttype':'none','savefig.facecolor':'white',
    })

def format_color(label):
    if 'DNA' in label or 'barcode BIN' in label:
        return DNA
    if 'backdune' in label.lower() or 'lighthouse' in label.lower():
        return ORANGE
    if label.startswith('GBIF') or 'Specimen' in label or 'specimen' in label:
        return ORANGE
    if 'Human' in label or "Perko" in label or 'UCSB Summer' in label or label.startswith('Ecdysis'):
        return ORANGE if 'lighthouse' in label.lower() else TEAL
    return GRAY
