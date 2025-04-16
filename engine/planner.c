#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "planner.h"
#include "engine.h"
#include "cairo_drawing.h"


void set_one_direction(int one_direction)
{
	config.one_direction = one_direction;
}


void set_debug(int debug) { config.debug = debug; }
void disable_fulls() { config.enable_fulls = 0; }
void disable_lux() { config.enable_lux = 0; }
void disable_splits() { config.enable_splits = 0; }
void disable_halves() { config.enable_halves = 0; }
void disable_quarters() { config.enable_quarters = 0; }
void set_lux_width(int width) { config.lux_width = width; }
void set_lux_height(int height) { config.lux_height = height; }


pnl_t* planner(room_t* room)
{
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


