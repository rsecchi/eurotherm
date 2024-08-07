#include "planner.h"
#include "engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>


pnl_t* planner(room_t* room)
{
	pnl_t *pnls=NULL, *pnl;
	panel_t *panels, *p;

	config.enable_quarters = 1;

	/* debug */
	transform_t trsf;
	trsf.origin = (point_t){320, 240};
	trsf.scale =(point_t){0.3, -0.3};
	canvas_t* cp = init_canvas(trsf);
	__debug_canvas = cp;
	draw_room(cp, room);
	/* ******* */

	__max_row_debug = 10000;
	panels = build_room(room);
	draw_panels(cp, panels);

	for(p=panels; p!=NULL; p=p->next) {
		pnl = malloc(sizeof(pnl_t));
		pnl->type = p->type;
		pnl->x = p->pos.x;
		pnl->y = p->pos.y;
		pnl->next = pnls;
		pnl->iso_flgs = p->orient_flags;
		pnl->dorsal_id = p->dorsal_id;

		pnls = pnl;
	}

	save_png(cp, "debug_output.png");
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


