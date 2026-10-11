"""Low-res draft: the plague year in Bishop Grandisson's register, week by week (matplotlib frames -> ffmpeg).
Feasibility only; the final version will be rebuilt in the episode's canvas style."""
import json, os, subprocess, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
sys.path.insert(0, '.')
from geocode import clean

OUT = 'frames'
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

d = pd.read_csv('institutions.csv').fillna('')
d = d[~d.place_raw.str.contains('Hants|Bosham|Sussex', regex=True)]
pl = pd.read_csv('places.csv').set_index('name')
d['name'] = d.place.map(clean)
d = d.join(pl[['lat', 'lon']], on='name').dropna(subset=['lat'])
d['dt'] = pd.to_datetime(d.date)
d = d.drop_duplicates(['place_raw', 'date'])
d = d[(d.lon > -6) & (d.lon < -2.8)]

land = json.load(open('sw_land.json'))
pollen = [(50.664, -4.034), (50.654, -4.013), (50.6125, -3.962), (50.978, -3.643), (51.171, -3.688), (51.107, -3.759),
          (50.970, -3.623), (50.934, -3.433), (51.139, -3.833), (51.117, -3.826), (51.131, -3.808), (51.129, -3.784),
          (50.656, -3.910), (50.975, -3.633), (50.623, -3.943)]

start, end = pd.Timestamp('1348-09-01'), pd.Timestamp('1350-06-30')
weeks = pd.date_range(start, end, freq='7D')
FPW = 4                       # frames per week at 24 fps -> 6 weeks/s
monthly = d.groupby(d.dt.dt.to_period('M')).size()
months = pd.period_range('1348-09', '1350-06', freq='M')
base = 30.5 / 12

fig = plt.figure(figsize=(9.6, 5.4), dpi=100, facecolor='#efe6d2')
ax = fig.add_axes([0.0, 0.25, 1.0, 0.75]); bx = fig.add_axes([0.06, 0.05, 0.88, 0.17])
lat0 = 50.6; kx = np.cos(np.radians(lat0))
fno = 0
for wi, w in enumerate(weeks):
    for sub in range(FPW):
        t = w + pd.Timedelta(days=7 * sub / FPW)
        ax.clear(); bx.clear()
        ax.set_facecolor('#d9cfb8')
        for ring in land:
            ax.add_patch(Polygon([(x * kx, y) for x, y in ring], closed=True, fc='#f4ecda', ec='#8a7a5c', lw=0.6))
        ax.set_xlim(-5.8 * kx, -2.85 * kx); ax.set_ylim(49.9, 51.32); ax.set_aspect('equal'); ax.axis('off')
        past = d[(d.dt >= start) & (d.dt <= t)]
        age = (t - past.dt).dt.days.values
        fresh = age < 21
        ax.scatter(past.lon[~fresh] * kx, past.lat[~fresh], s=7, c='#7a2a1a', alpha=0.35, lw=0)
        a = np.clip(1 - age[fresh] / 21, 0, 1)
        if fresh.any(): ax.scatter(past.lon[fresh] * kx, past.lat[fresh], s=10 + 60 * a, c='#c0301a', alpha=0.25 + 0.7 * a, lw=0)
        py, px = zip(*pollen)
        ax.scatter(np.array(px) * kx, py, marker='^', s=26, facecolors='none', edgecolors='#2d5a3a', lw=1.1)
        ax.scatter([-3.60 * kx], [50.603], marker='*', s=70, c='#1b2a4a')
        ax.text(-3.57 * kx, 50.62, 'Chudleigh (the bishop)', fontsize=8, color='#1b2a4a', family='serif')
        ax.text(-5.75 * kx, 51.2, t.strftime('%B %Y') if t.year != 1348 or t.month > 2 else '', fontsize=20, family='serif', color='#2b2216')
        n = int((past.dt >= start).sum())
        ax.text(-5.75 * kx, 51.08, f'{n} new priests instituted since Sept 1348', fontsize=10, family='serif', color='#7a2a1a')
        ax.text(-5.75 * kx, 50.98, '△ pollen sites (Izdebski et al. 2022)', fontsize=8, family='serif', color='#2d5a3a')
        ax.text(-3.0 * kx, 49.97, 'Source: Register of Bp. Grandisson, ed. Hingeston-Randolph 1899 · draft', fontsize=6.5, ha='right', color='#6b5d45')
        # monthly bars up to now
        vals = [monthly.get(m, 0) if m.to_timestamp() <= t else 0 for m in months]
        bx.bar(range(len(months)), vals, color='#7a2a1a', width=0.8)
        bx.axhline(base, color='#2b2216', lw=0.8, ls='--')
        bx.text(len(months) - 0.5, base + 2, 'normal month ≈ 2.5', fontsize=7, ha='right', family='serif')
        bx.set_ylim(0, 62); bx.set_xlim(-0.6, len(months) - 0.4)
        bx.set_xticks(range(0, len(months), 3)); bx.set_xticklabels([m.strftime('%b %y') for m in months[::3]], fontsize=7)
        bx.set_yticks([]); [s.set_visible(False) for k, s in bx.spines.items() if k != 'bottom']
        bx.set_facecolor('#efe6d2')
        fig.savefig(f'{OUT}/f{fno:05d}.png', facecolor=fig.get_facecolor()); fno += 1
print(fno, 'frames')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', f'{OUT}/f%05d.png', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-crf', '24', 'register_map_1348_1350.mp4'], check=True)
print('done')
