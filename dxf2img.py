import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import Properties, LayoutProperties

import sys

name = sys.argv[1]

img_format = '.png'
img_res = 300

doc = ezdxf.readfile(name)
msp = doc.modelspace()

fig = plt.figure()
ax = fig.add_axes([0, 0, 1, 1])
ctx = RenderContext(doc)
ctx.set_current_layout(msp)
#ctx.current_layout_properties.has_dark_background = False
#ctx.current_layout_properties.background_color = '#00FFFF'
#ctx.current_layout_properties.set_colors(bg='#00FF00')
#print(ctx.current_layout_properties.background_color)
out = MatplotlibBackend(ax)

# Better control over the LayoutProperties used by the drawing frontend
layout_properties = LayoutProperties.from_layout(msp)
layout_properties.set_colors(bg='#FFFFFF')

Frontend(ctx, out).draw_layout(msp, layout_properties=layout_properties, finalize=True)

image = name[:-4] + img_format
fig.savefig(image, dpi=img_res)





