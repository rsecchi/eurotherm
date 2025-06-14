#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "planner.h"
#include "engine.h"
#include "cairo_drawing.h"


pnl_t* planner(room_t* room, config_t* pconf)
{

	if (pconf) {
		config.debug = pconf->debug;
		config.enable_fulls = pconf->enable_fulls;
		config.enable_lux = pconf->enable_lux;
		config.enable_splits = pconf->enable_splits;
		config.enable_halves = pconf->enable_halves;
		config.enable_quarters = pconf->enable_quarters;
		config.max_row_debug = pconf->max_row_debug;
		config.debug_animation = pconf->debug_animation;
		config.one_direction = pconf->one_direction;
		config.lux_width = pconf->lux_width;
		config.lux_height = pconf->lux_height;
	}	

	pnl_t *pnls=NULL, *pnl;
	panel_t *panels, *p;
	transform_t trsf;

	if (config.debug) {
		trsf.origin = (point_t){320, 240};
		trsf.scale =(point_t){0.8, -0.8};
		init_canvas(trsf);
		/* draw_room(room); */
	}

	panels = build_room(room);

	/* strip private panel_t fields */
	for(p=panels; p!=NULL; p=p->next) {
		pnl = malloc(sizeof(pnl_t));
		pnl->type = p->type;
		pnl->x = p->pos.x;
		pnl->y = p->pos.y;
		pnl->next = pnls;
		pnl->iso_flgs = p->orient_flags;
		pnl->dorsal_row = p->dorsal_row;
		pnls = pnl;
	}

	if (config.debug) {
		/* draw_panels(panels); */
		save_png("debug_output.png");
	}
	return  pnls;
}


void free_list(pnl_t* head)
{
pnl_t *p, *q;
	p=head;
	while(p!=NULL) {
		q = p->next;
		free(p);
		p = q;
	}
}

void print(pnl_t* head)
{
	for(pnl_t* p=head; p!=NULL; p=p->next) {
		printf("%s\n", panel_desc[p->type].name);
	}
}


