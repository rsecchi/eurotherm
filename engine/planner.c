#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "planner.h"
#include "engine.h"
#include "cairo_drawing.h"


pnl_t* planner(room_t* room)
{
	pnl_t *pnls=NULL, *pnl;
	panel_t *panels, *p;
	transform_t trsf;

	check_config();

	if (config.debug) {
		trsf.origin = (point_t){320, 240};
		trsf.scale =(point_t){0.3, -0.3};
		init_canvas(trsf);
		/* draw_room(room); */
	}

	panels = build_room(room);

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


